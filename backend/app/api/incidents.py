"""Incident endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongo import get_database
from app.models.incident import IncidentStatus, Priority
from app.schemas.incident import (
    IncidentCreateRequest,
    IncidentReopenRequest,
    IncidentResolveRequest,
    IncidentResponse,
    IncidentUpdateRequest,
)
from app.services import incident_service, resolution_service

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


@router.get("")
async def list_incidents(
    status_: Optional[IncidentStatus] = Query(None, alias="status"),
    priority: Optional[Priority] = Query(None),
    category: Optional[str] = Query(None),
    service: Optional[str] = Query(None),
    team: Optional[str] = Query(None),
    assignee_id: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    filters = {
        "status": status_.value if status_ else None,
        "priority": priority.value if priority else None,
        "category": category,
        "service": service,
        "team": team,
        "assignee_id": assignee_id,
        "date_from": date_from,
        "date_to": date_to,
        "search": search,
    }
    return await incident_service.list_incidents(db, filters=filters, page=page, page_size=page_size)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_incident(payload: IncidentCreateRequest, db: AsyncIOMotorDatabase = Depends(get_database)):
    doc = payload.model_dump(mode="json")
    created = await incident_service.create_incident(db, doc)
    return created


@router.get("/{incident_id}")
async def get_incident(incident_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    return await incident_service.get_incident(db, incident_id)


@router.patch("/{incident_id}")
async def update_incident(incident_id: str, payload: IncidentUpdateRequest, db: AsyncIOMotorDatabase = Depends(get_database)):
    updates = payload.model_dump(mode="json", exclude_unset=True)
    return await incident_service.update_incident(db, incident_id, updates)


@router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_incident(incident_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    await incident_service.delete_incident(db, incident_id)


@router.post("/{incident_id}/reopen")
async def reopen_incident(incident_id: str, payload: IncidentReopenRequest, db: AsyncIOMotorDatabase = Depends(get_database)):
    return await incident_service.reopen_incident(db, incident_id, payload.target_status.value, payload.reason)


@router.post("/{incident_id}/resolve")
async def resolve_incident(incident_id: str, payload: IncidentResolveRequest, db: AsyncIOMotorDatabase = Depends(get_database)):
    return await resolution_service.resolve_incident(
        db,
        incident_id,
        root_cause=payload.root_cause,
        resolution_description=payload.resolution_description,
        resolved_by=payload.resolved_by,
    )
