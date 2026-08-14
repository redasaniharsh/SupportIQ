"""Pinecone client wrapper.

One index "ai-service-desk", namespaces "knowledge" and "historical-tickets",
integrated embedding model "llama-text-embed-v2", cosine metric.

The official `pinecone` SDK is synchronous; we wrap the blocking calls with
`asyncio.to_thread` so the rest of the app can stay async without needing a
separate async HTTP client just for this.
"""
from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import Any, Optional

from app.core.config import Settings, get_settings
from app.core.exceptions import RetrievalError
from app.core.logging import get_logger
from app.vector.metadata import NAMESPACE_HISTORICAL, NAMESPACE_KNOWLEDGE

logger = get_logger(__name__)

EMBEDDING_FIELD_MAP = {"text": "text"}


class PineconeClientWrapper:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self._pc = None
        self._index = None

    def _get_pc(self):
        if self._pc is None:
            from pinecone import Pinecone

            if not self.settings.pinecone_api_key:
                raise RetrievalError("PINECONE_API_KEY is not configured.")
            self._pc = Pinecone(api_key=self.settings.pinecone_api_key)
        return self._pc

    def _index_exists_sync(self) -> bool:
        pc = self._get_pc()
        existing = [idx["name"] for idx in pc.list_indexes()]
        return self.settings.pinecone_index_name in existing

    def _create_index_sync(self) -> None:
        pc = self._get_pc()
        pc.create_index_for_model(
            name=self.settings.pinecone_index_name,
            cloud=self.settings.pinecone_cloud,
            region=self.settings.pinecone_region,
            embed={
                "model": self.settings.embedding_model,
                "field_map": EMBEDDING_FIELD_MAP,
                "metric": "cosine",
            },
        )

    def _get_index_sync(self):
        if self._index is None:
            pc = self._get_pc()
            self._index = pc.Index(self.settings.pinecone_index_name)
        return self._index

    async def ensure_index(self) -> bool:
        """Creates the index if it does not exist. Returns True if it was created."""
        exists = await asyncio.to_thread(self._index_exists_sync)
        if exists:
            return False
        await asyncio.to_thread(self._create_index_sync)
        logger.info("pinecone_index_created", extra={"index": self.settings.pinecone_index_name})
        return True

    async def upsert_records(self, namespace: str, records: list[dict[str, Any]]) -> None:
        """`records` are dicts with at least `_id` and `text` (integrated
        embedding field) plus small metadata fields, matching upsert_records'
        expected shape."""
        index = await asyncio.to_thread(self._get_index_sync)
        try:
            await asyncio.to_thread(index.upsert_records, namespace=namespace, records=records)
        except Exception as exc:  # pragma: no cover - network dependent
            logger.error("pinecone_upsert_failed", extra={"error": str(exc)})
            raise RetrievalError(f"Pinecone upsert failed: {exc}") from exc

    async def search(
        self,
        *,
        namespace: str,
        query_text: str,
        top_k: int = 10,
        filter: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        index = await asyncio.to_thread(self._get_index_sync)
        query: dict[str, Any] = {"inputs": {"text": query_text}, "top_k": top_k}
        if filter:
            query["filter"] = filter
        try:
            result = await asyncio.to_thread(
                index.search,
                namespace=namespace,
                query=query,
                fields=["text", "document_id", "document_type", "category", "service", "priority", "chunk_index", "source", "title", "has_resolution"],
            )
        except Exception as exc:  # pragma: no cover - network dependent
            logger.error("pinecone_search_failed", extra={"error": str(exc), "namespace": namespace})
            raise RetrievalError(f"Pinecone search failed: {exc}") from exc

        hits = result.get("result", {}).get("hits", []) if isinstance(result, dict) else getattr(result, "result", {}).get("hits", [])
        normalized = []
        for hit in hits:
            fields = hit.get("fields", {})
            normalized.append(
                {
                    "id": hit.get("_id"),
                    "score": hit.get("_score", 0.0),
                    "text": fields.get("text", ""),
                    "metadata": {k: v for k, v in fields.items() if k != "text"},
                }
            )
        return normalized

    async def describe_index_stats(self) -> dict[str, Any]:
        index = await asyncio.to_thread(self._get_index_sync)
        try:
            stats = await asyncio.to_thread(index.describe_index_stats)
            return stats.to_dict() if hasattr(stats, "to_dict") else dict(stats)
        except Exception as exc:  # pragma: no cover
            raise RetrievalError(f"Pinecone describe_index_stats failed: {exc}") from exc

    async def delete_namespace(self, namespace: str) -> None:
        index = await asyncio.to_thread(self._get_index_sync)
        try:
            await asyncio.to_thread(index.delete, namespace=namespace, delete_all=True)
        except Exception as exc:  # pragma: no cover
            logger.warning("pinecone_delete_namespace_failed", extra={"error": str(exc), "namespace": namespace})

    async def delete_index(self) -> None:
        pc = await asyncio.to_thread(self._get_pc)
        try:
            await asyncio.to_thread(pc.delete_index, self.settings.pinecone_index_name)
        except Exception as exc:  # pragma: no cover
            logger.warning("pinecone_delete_index_failed", extra={"error": str(exc)})


@lru_cache
def get_pinecone_client() -> PineconeClientWrapper:
    return PineconeClientWrapper()
