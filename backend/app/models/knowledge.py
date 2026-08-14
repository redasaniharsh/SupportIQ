"""Knowledge article model — mirrors DESIGN.md section 5.3."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.utils.dates import utcnow


class KnowledgeArticle(BaseModel):
    article_id: str  # e.g. "KB-001"
    title: str
    category: str
    service: Optional[str] = None
    symptoms: list[str] = Field(default_factory=list)
    root_causes: list[str] = Field(default_factory=list)
    troubleshooting_steps: list[str] = Field(default_factory=list)
    resolution: str
    escalation_conditions: list[str] = Field(default_factory=list)
    version: int = 1
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
