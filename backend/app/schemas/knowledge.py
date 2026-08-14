"""Knowledge article request/response schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class KnowledgeCreateRequest(BaseModel):
    title: str = Field(..., min_length=3)
    category: str
    service: Optional[str] = None
    symptoms: list[str] = Field(default_factory=list)
    root_causes: list[str] = Field(default_factory=list)
    troubleshooting_steps: list[str] = Field(default_factory=list)
    resolution: str
    escalation_conditions: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class KnowledgeResponse(BaseModel):
    article_id: str
    title: str
    category: str
    service: Optional[str] = None
    symptoms: list[str]
    root_causes: list[str]
    troubleshooting_steps: list[str]
    resolution: str
    escalation_conditions: list[str]
    version: int
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeFilters(BaseModel):
    category: Optional[str] = None
    service: Optional[str] = None
    search: Optional[str] = None
