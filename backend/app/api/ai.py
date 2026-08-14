"""AI analysis + similar-incidents endpoints (still under /api/incidents/{id}/...
per DESIGN.md section 7, kept in a dedicated module for clarity)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongo import get_database
from app.services import incident_service, similarity_service
from app.services.ai_service import run_analysis

router = APIRouter(prefix="/api/incidents", tags=["ai"])


@router.post("/{incident_id}/analyze")
async def analyze_incident(incident_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    incident = await incident_service.get_incident(db, incident_id)
    result = await run_analysis(db, incident)
    return result


@router.get("/{incident_id}/similar")
async def similar_incidents(incident_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    incident = await incident_service.get_incident(db, incident_id)
    return await similarity_service.find_similar_incidents(incident)
