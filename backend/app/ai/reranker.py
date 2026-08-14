"""Deterministic lightweight reranker, per DESIGN.md section 6.3 step 5.

Combines: semantic score (from Pinecone), category/service match, presence
of a resolution, and lexical overlap with the query. This only reorders
retrieved evidence — it never invents content or an answer.
"""
from __future__ import annotations

from typing import Any

from app.utils.text import lexical_overlap_score

WEIGHT_SEMANTIC = 0.55
WEIGHT_CATEGORY_MATCH = 0.15
WEIGHT_HAS_RESOLUTION = 0.10
WEIGHT_LEXICAL_OVERLAP = 0.20


def rerank(
    candidates: list[dict[str, Any]],
    *,
    query_text: str,
    category: str | None = None,
    service: str | None = None,
) -> list[dict[str, Any]]:
    """Returns candidates sorted by a deterministic composite score.

    Each candidate dict is expected to have: score (semantic similarity),
    metadata (dict with optional category/service/priority/source), and
    text (the chunk text used for lexical overlap).
    """
    scored = []
    for candidate in candidates:
        metadata = candidate.get("metadata", {}) or {}
        semantic = float(candidate.get("score", 0.0) or 0.0)

        category_match = 0.0
        if category and metadata.get("category") and metadata["category"].lower() == category.lower():
            category_match = 1.0
        if service and metadata.get("service") and metadata["service"].lower() == (service or "").lower():
            category_match = max(category_match, 0.5)

        has_resolution = 1.0 if metadata.get("has_resolution") or metadata.get("resolution") else 0.0

        lexical = lexical_overlap_score(query_text, candidate.get("text", ""))

        composite = (
            WEIGHT_SEMANTIC * semantic
            + WEIGHT_CATEGORY_MATCH * category_match
            + WEIGHT_HAS_RESOLUTION * has_resolution
            + WEIGHT_LEXICAL_OVERLAP * lexical
        )

        enriched = dict(candidate)
        enriched["rerank_score"] = round(composite, 4)
        scored.append(enriched)

    scored.sort(key=lambda c: c["rerank_score"], reverse=True)
    return scored
