"""Thin service wrapper around the vector retrieval pipeline.

Kept separate from `ai_service.py` so the retrieval step can be unit tested
and reused (e.g. by the /search endpoint) independently of LLM orchestration.
"""
from __future__ import annotations

from typing import Any, Optional

from app.core.config import Settings, get_settings
from app.vector.pinecone_client import PineconeClientWrapper, get_pinecone_client
from app.vector.retriever import RetrievalPipeline


def get_retrieval_pipeline(
    client: Optional[PineconeClientWrapper] = None, settings: Optional[Settings] = None
) -> RetrievalPipeline:
    return RetrievalPipeline(client=client or get_pinecone_client(), settings=settings or get_settings())


async def retrieve_evidence_for_incident(incident: dict[str, Any], *, pipeline: Optional[RetrievalPipeline] = None) -> dict[str, Any]:
    pipeline = pipeline or get_retrieval_pipeline()
    return await pipeline.retrieve_evidence(incident)
