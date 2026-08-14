"""Incident model — mirrors DESIGN.md section 5.1 JSON shape."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from app.models.category import CategoryRef
from app.utils.dates import utcnow


class IncidentStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING = "pending"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Priority(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


# Forward transitions allowed without an explicit "reopen" action.
ALLOWED_TRANSITIONS: dict[IncidentStatus, set[IncidentStatus]] = {
    IncidentStatus.OPEN: {IncidentStatus.IN_PROGRESS, IncidentStatus.PENDING, IncidentStatus.RESOLVED},
    IncidentStatus.IN_PROGRESS: {IncidentStatus.PENDING, IncidentStatus.RESOLVED, IncidentStatus.OPEN},
    IncidentStatus.PENDING: {IncidentStatus.IN_PROGRESS, IncidentStatus.RESOLVED, IncidentStatus.OPEN},
    IncidentStatus.RESOLVED: {IncidentStatus.CLOSED, IncidentStatus.IN_PROGRESS},
    IncidentStatus.CLOSED: set(),  # closed -> anything requires explicit reopen
}


class Assignment(BaseModel):
    team: Optional[str] = None
    assignee_id: Optional[str] = None


class SourceInfo(BaseModel):
    type: str = "manual"  # "manual" | "dataset"
    dataset: Optional[str] = None
    record_id: Optional[str] = None


class AIInfo(BaseModel):
    last_analysis_id: Optional[str] = None
    analyzed_at: Optional[datetime] = None
    confidence: Optional[str] = None  # High/Medium/Low bucket, computed server-side


class Resolution(BaseModel):
    root_cause: Optional[str] = None
    description: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None


class Incident(BaseModel):
    incident_id: str
    title: str
    description: str
    status: IncidentStatus = IncidentStatus.OPEN
    priority: Priority = Priority.P3
    category: CategoryRef
    assignment: Assignment = Field(default_factory=Assignment)
    source: SourceInfo = Field(default_factory=SourceInfo)
    ai: AIInfo = Field(default_factory=AIInfo)
    resolution: Resolution = Field(default_factory=Resolution)
    source_data: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    def to_mongo(self) -> dict:
        doc = self.model_dump(mode="python")
        return doc


def is_valid_transition(current: IncidentStatus, target: IncidentStatus) -> bool:
    if current == target:
        return True
    return target in ALLOWED_TRANSITIONS.get(current, set())
