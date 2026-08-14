"""Similar-incident detection service (DESIGN.md section 6.4)."""
from __future__ import annotations

from typing import Any, Optional

from app.core.config import Settings, get_settings
from app.services.retrieval_service import get_retrieval_pipeline
from app.vector.retriever import RetrievalPipeline


async def find_similar_incidents(
    incident: dict[str, Any],
    *,
    pipeline: Optional[RetrievalPipeline] = None,
    settings: Optional[Settings] = None,
) -> dict[str, Any]:
    settings = settings or get_settings()
    pipeline = pipeline or get_retrieval_pipeline(settings=settings)
    items = await pipeline.find_similar_incidents(incident, exclude_incident_id=incident.get("incident_id"))
    return {
        "incident_id": incident.get("incident_id"),
        "duplicate_threshold": settings.similarity_duplicate_threshold,
        "related_threshold": settings.similarity_related_threshold,
        "items": items,
    }
