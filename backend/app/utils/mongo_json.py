"""Helpers for making raw Mongo documents JSON-serializable by FastAPI.

Mongo documents include a `_id` ObjectId field that FastAPI/Pydantic cannot
serialize by default. Since every document already carries its own
domain-level ID (incident_id, comment_id, article_id, analysis_id, ...), we
simply drop `_id` before returning documents from API endpoints.
"""
from __future__ import annotations

from typing import Any


def strip_id(doc: dict[str, Any] | None) -> dict[str, Any] | None:
    if doc is None:
        return None
    doc = dict(doc)
    doc.pop("_id", None)
    return doc


def strip_ids(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [strip_id(doc) for doc in docs]
