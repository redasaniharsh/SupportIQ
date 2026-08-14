"""Pinecone vector metadata shape helpers.

Per DESIGN.md 6.2, metadata per vector is kept small:
document_id, document_type, category, service, priority?, chunk_index,
source, title. Never the full Mongo document.
"""
from __future__ import annotations

from typing import Any, Optional

DOCUMENT_TYPE_KNOWLEDGE = "knowledge"
DOCUMENT_TYPE_HISTORICAL = "historical-tickets"

NAMESPACE_KNOWLEDGE = "knowledge"
NAMESPACE_HISTORICAL = "historical-tickets"


def build_metadata(
    *,
    document_id: str,
    document_type: str,
    category: Optional[str],
    service: Optional[str],
    chunk_index: int,
    source: str,
    title: str,
    priority: Optional[str] = None,
    has_resolution: bool = False,
    text: Optional[str] = None,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "document_id": document_id,
        "document_type": document_type,
        "category": category or "unknown",
        "service": service or "unknown",
        "chunk_index": chunk_index,
        "source": source,
        "title": title[:200] if title else "",
        "has_resolution": bool(has_resolution),
    }
    if priority:
        metadata["priority"] = priority
    if text is not None:
        # Pinecone integrated embedding requires the source text field.
        metadata["text"] = text
    return metadata
