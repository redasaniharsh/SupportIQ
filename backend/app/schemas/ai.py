"""API-level schemas for AI analysis and similar-incident endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel

from app.ai.schemas import AIAnalysisResponse
from app.models.ai_analysis import ConfidenceInfo, EvidenceRef


class AnalyzeSuccessResponse(BaseModel):
    status: Literal["ok"] = "ok"
    analysis_id: str
    incident_id: str
    model: str
    prompt_version: str
    analysis: AIAnalysisResponse
    evidence: list[EvidenceRef]
    confidence: ConfidenceInfo
    retrieval_count: int
    latency_ms: int
    created_at: datetime


class AnalyzeUnavailableResponse(BaseModel):
    status: Literal["ai_unavailable"] = "ai_unavailable"
    message: str
    retryable: bool = True


class SimilarIncidentItem(BaseModel):
    incident_id: str
    title: str
    similarity: float
    relationship: Literal["duplicate", "related"]
    status: Optional[str] = None
    resolution_summary: Optional[str] = None


class SimilarIncidentsResponse(BaseModel):
    incident_id: str
    duplicate_threshold: float
    related_threshold: float
    items: list[SimilarIncidentItem]
