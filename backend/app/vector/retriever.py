"""Retrieval + fallback broadening + dedupe + rerank pipeline.

Implements DESIGN.md sections 6.3 (retrieval) and 6.4 (similar-incident
detection).
"""
from __future__ import annotations

from typing import Any, Optional

from app.ai.reranker import rerank
from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.vector.metadata import NAMESPACE_HISTORICAL, NAMESPACE_KNOWLEDGE
from app.vector.pinecone_client import PineconeClientWrapper

logger = get_logger(__name__)

TOP_K_PER_NAMESPACE = 10
FINAL_EVIDENCE_MIN = 5
FINAL_EVIDENCE_MAX = 8
THIN_RESULTS_THRESHOLD = 3  # fewer than this triggers fallback broadening


def _build_query_text(incident: dict[str, Any]) -> str:
    parts = [
        incident.get("title", ""),
        incident.get("description", ""),
    ]
    category = incident.get("category") or {}
    if isinstance(category, dict) and category.get("name"):
        parts.append(category["name"])
    return " ".join(p for p in parts if p)


def _dedupe_by_document(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    deduped = []
    for candidate in candidates:
        doc_id = candidate.get("metadata", {}).get("document_id") or candidate.get("id")
        if doc_id in seen:
            continue
        seen.add(doc_id)
        deduped.append(candidate)
    return deduped


async def _search_with_fallback(
    client: PineconeClientWrapper,
    *,
    namespace: str,
    query_text: str,
    category: Optional[str],
    service: Optional[str],
    top_k: int = TOP_K_PER_NAMESPACE,
) -> list[dict[str, Any]]:
    """Search with progressive fallback broadening: category+service filter
    -> category-only filter -> no filter (global search)."""
    filters_to_try: list[Optional[dict[str, Any]]] = []
    if category and service:
        filters_to_try.append({"category": category, "service": service})
    if category:
        filters_to_try.append({"category": category})
    filters_to_try.append(None)

    results: list[dict[str, Any]] = []
    for filt in filters_to_try:
        try:
            results = await client.search(namespace=namespace, query_text=query_text, top_k=top_k, filter=filt)
        except Exception as exc:
            logger.warning("namespace_search_failed", extra={"namespace": namespace, "error": str(exc)})
            results = []
        if len(results) >= THIN_RESULTS_THRESHOLD:
            break
    return results


class RetrievalPipeline:
    def __init__(self, client: Optional[PineconeClientWrapper] = None, settings: Optional[Settings] = None):
        self.client = client
        self.settings = settings or get_settings()

    async def retrieve_evidence(self, incident: dict[str, Any]) -> dict[str, Any]:
        """Returns {"knowledge_evidence": [...], "historical_evidence": [...],
        "retrieval_count": int} where each evidence item has evidence_id,
        text, source, title, score, document_id, document_type."""
        query_text = _build_query_text(incident)
        category = (incident.get("category") or {}).get("name")
        service = (incident.get("category") or {}).get("service")

        knowledge_raw = await _search_with_fallback(
            self.client, namespace=NAMESPACE_KNOWLEDGE, query_text=query_text, category=category, service=service
        )
        historical_raw = await _search_with_fallback(
            self.client, namespace=NAMESPACE_HISTORICAL, query_text=query_text, category=category, service=service
        )

        knowledge_deduped = _dedupe_by_document(knowledge_raw)
        historical_deduped = _dedupe_by_document(historical_raw)

        knowledge_ranked = rerank(knowledge_deduped, query_text=query_text, category=category, service=service)
        historical_ranked = rerank(historical_deduped, query_text=query_text, category=category, service=service)

        combined_limit = FINAL_EVIDENCE_MAX
        half = combined_limit // 2
        knowledge_final = knowledge_ranked[:half] or knowledge_ranked[:FINAL_EVIDENCE_MIN]
        historical_final = historical_ranked[: combined_limit - len(knowledge_final)]

        def _to_evidence(item: dict[str, Any], document_type: str) -> dict[str, Any]:
            metadata = item.get("metadata", {})
            return {
                "evidence_id": item["id"],
                "document_id": metadata.get("document_id"),
                "document_type": document_type,
                "text": item.get("text", ""),
                "title": metadata.get("title", ""),
                "source": metadata.get("source", document_type),
                "score": item.get("rerank_score", item.get("score", 0.0)),
            }

        knowledge_evidence = [_to_evidence(i, "knowledge") for i in knowledge_final]
        historical_evidence = [_to_evidence(i, "historical-tickets") for i in historical_final]

        return {
            "knowledge_evidence": knowledge_evidence,
            "historical_evidence": historical_evidence,
            "retrieval_count": len(knowledge_evidence) + len(historical_evidence),
        }

    async def find_similar_incidents(
        self, incident: dict[str, Any], *, exclude_incident_id: Optional[str] = None, top_k: int = 10
    ) -> list[dict[str, Any]]:
        """Cosine similarity search against historical-tickets namespace,
        bucketed into duplicate/related per env-configurable thresholds."""
        query_text = _build_query_text(incident)
        raw = await self.client.search(namespace=NAMESPACE_HISTORICAL, query_text=query_text, top_k=top_k)
        deduped = _dedupe_by_document(raw)

        results = []
        for item in deduped:
            metadata = item.get("metadata", {})
            document_id = metadata.get("document_id")
            if exclude_incident_id and document_id == exclude_incident_id:
                continue
            score = float(item.get("score", 0.0))
            if score >= self.settings.similarity_duplicate_threshold:
                relationship = "duplicate"
            elif score >= self.settings.similarity_related_threshold:
                relationship = "related"
            else:
                continue  # below related threshold: not shown at all
            results.append(
                {
                    "incident_id": document_id,
                    "title": metadata.get("title", ""),
                    "similarity": round(score, 4),
                    "relationship": relationship,
                }
            )
        return results
