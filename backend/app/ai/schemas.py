"""Pydantic schema for the structured LLM output, per DESIGN.md 6.5 /
assessment spec.

The LLM must return exactly this shape as JSON. Anything else fails
validation and is treated as an AI service error (never silently coerced
into something that could look like ground truth).
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

ConfidenceLevel = Literal["High", "Medium", "Low"]


class ProbableCause(BaseModel):
    cause: str
    evidence_ids: list[str] = Field(default_factory=list)
    likelihood: Literal["High", "Medium", "Low"] = "Medium"


class RecommendedAction(BaseModel):
    action: str
    evidence_ids: list[str] = Field(default_factory=list)
    priority_order: int = 1


class SimilarIncidentMention(BaseModel):
    incident_id: str
    evidence_id: str
    relationship: Literal["duplicate", "related"] = "related"
    rationale: str | None = None


class KnowledgeArticleMention(BaseModel):
    article_id: str
    evidence_id: str
    relevance: str | None = None


class AIAnalysisResponse(BaseModel):
    """The exact structured JSON object the LLM must return."""

    summary: str
    category: str
    priority: Literal["P1", "P2", "P3", "P4"]
    probable_causes: list[ProbableCause] = Field(default_factory=list)
    recommended_actions: list[RecommendedAction] = Field(default_factory=list)
    similar_incidents: list[SimilarIncidentMention] = Field(default_factory=list)
    knowledge_articles: list[KnowledgeArticleMention] = Field(default_factory=list)
    escalation_required: bool = False
    confidence: ConfidenceLevel = "Medium"
    uncertainties: list[str] = Field(default_factory=list)
    final_recommendation: str

    @field_validator("summary", "final_recommendation")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("must not be blank")
        return v.strip()
