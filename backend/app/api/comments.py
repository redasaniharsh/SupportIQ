"""Comment endpoints, nested under an incident."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db import collections as c
from app.db.mongo import get_database
from app.schemas.comment import CommentCreateRequest
from app.services import incident_service
from app.utils.dates import utcnow
from app.utils.mongo_json import strip_ids
from app.utils.pagination import build_page_envelope, clamp_pagination, compute_skip

router = APIRouter(prefix="/api/incidents", tags=["comments"])


@router.get("/{incident_id}/comments")
async def list_comments(
    incident_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    await incident_service.get_incident(db, incident_id)  # 404s if missing
    page, page_size = clamp_pagination(page, page_size)
    query = {"incident_id": incident_id}
    total = await db[c.COMMENTS].count_documents(query)
    cursor = db[c.COMMENTS].find(query).sort("created_at", 1).skip(compute_skip(page, page_size)).limit(page_size)
    items = strip_ids([doc async for doc in cursor])
    return build_page_envelope(items, page=page, page_size=page_size, total=total)


@router.post("/{incident_id}/comments", status_code=status.HTTP_201_CREATED)
async def create_comment(incident_id: str, payload: CommentCreateRequest, db: AsyncIOMotorDatabase = Depends(get_database)):
    await incident_service.get_incident(db, incident_id)  # 404s if missing
    import uuid

    doc = {
        "comment_id": f"CMT-{uuid.uuid4().hex[:12]}",
        "incident_id": incident_id,
        "author": payload.author,
        "author_id": payload.author_id,
        "body": payload.body,
        "is_internal": payload.is_internal,
        "created_at": utcnow(),
    }
    await db[c.COMMENTS].insert_one(dict(doc))
    await db[c.INCIDENTS].update_one({"incident_id": incident_id}, {"$set": {"updated_at": utcnow()}})
    return doc
