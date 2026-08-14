"""Cross-collection search endpoint (incidents + knowledge articles).

Uses indexed Mongo text search, never full-collection scans in Python.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db import collections as c
from app.db.mongo import get_database
from app.utils.mongo_json import strip_ids
from app.utils.pagination import clamp_pagination, compute_skip

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("")
async def search(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    page, page_size = clamp_pagination(page, page_size)
    skip = compute_skip(page, page_size)

    incident_query = {"$text": {"$search": q}}
    knowledge_query = {"$text": {"$search": q}}

    incident_total = await db[c.INCIDENTS].count_documents(incident_query)
    knowledge_total = await db[c.KNOWLEDGE_ARTICLES].count_documents(knowledge_query)

    incident_cursor = (
        db[c.INCIDENTS]
        .find(incident_query, {"score": {"$meta": "textScore"}})
        .sort([("score", {"$meta": "textScore"})])
        .skip(skip)
        .limit(page_size)
    )
    knowledge_cursor = (
        db[c.KNOWLEDGE_ARTICLES]
        .find(knowledge_query, {"score": {"$meta": "textScore"}})
        .sort([("score", {"$meta": "textScore"})])
        .skip(skip)
        .limit(page_size)
    )

    incidents = strip_ids([doc async for doc in incident_cursor])
    knowledge = strip_ids([doc async for doc in knowledge_cursor])

    return {
        "query": q,
        "incidents": {"items": incidents, "total": incident_total},
        "knowledge_articles": {"items": knowledge, "total": knowledge_total},
        "page": page,
        "page_size": page_size,
    }
