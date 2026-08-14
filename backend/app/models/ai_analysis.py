"""ai_analyses collection document — mirrors DESIGN.md section 5.4."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.utils.dates import utcnow

PROMPT_VERSION = "service-desk-analysis-v1"


class EvidenceRef(BaseModel):
    evidence_id: str
    document_type: str  # "knowledge" | "historical-tickets"
    document_id: str
    title: Optional[str] = None
    score: Optional[float] = None
    source: Optional[str] = None


class ConfidenceInfo(BaseModel):
    model_reported: Optional[str] = None  # LLM self-report, presentation only
    evidence_score: float  # backend-computed, 0..1
    bucket: str  # High | Medium | Low, backend-computed


class AIAnalysisRecord(BaseModel):
    analysis_id: str
    incident_id: str
    prompt_version: str = PROMPT_VERSION
    model: str
    response: dict  # the validated AIAnalysisResponse payload (as dict)
    evidence: list[EvidenceRef] = Field(default_factory=list)
    confidence: ConfidenceInfo
    retrieval_count: int = 0
    latency_ms: int = 0
    created_at: datetime = Field(default_factory=utcnow)
