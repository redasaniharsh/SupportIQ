"""Incident request/response schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.models.category import CategoryRef
from app.models.incident import Assignment, IncidentStatus, Priority, Resolution


class IncidentCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=300)
    description: str = Field(..., min_length=1)
    category: CategoryRef
    priority: Priority = Priority.P3
    assignment: Optional[Assignment] = None

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("title must not be blank")
        return v


class IncidentUpdateRequest(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=300)
    description: Optional[str] = None
    status: Optional[IncidentStatus] = None
    priority: Optional[Priority] = None
    category: Optional[CategoryRef] = None
    assignment: Optional[Assignment] = None


class IncidentResolveRequest(BaseModel):
    root_cause: str = Field(..., min_length=3)
    resolution_description: str = Field(..., min_length=3)
    resolved_by: str = Field(..., min_length=1)


class IncidentReopenRequest(BaseModel):
    reason: Optional[str] = None
    target_status: IncidentStatus = IncidentStatus.IN_PROGRESS


class IncidentResponse(BaseModel):
    incident_id: str
    title: str
    description: str
    status: IncidentStatus
    priority: Priority
    category: CategoryRef
    assignment: Assignment
    ai: dict
    resolution: Resolution
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IncidentFilters(BaseModel):
    status: Optional[IncidentStatus] = None
    priority: Optional[Priority] = None
    category: Optional[str] = None
    service: Optional[str] = None
    team: Optional[str] = None
    assignee_id: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search: Optional[str] = None
