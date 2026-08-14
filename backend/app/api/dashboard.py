"""Dashboard analytics endpoint — aggregation queries only, never Python-side
full-collection scans."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db import collections as c
from app.db.mongo import get_database

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
async def dashboard_stats(db: AsyncIOMotorDatabase = Depends(get_database)):
    total_incidents = await db[c.INCIDENTS].count_documents({})

    status_pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    priority_pipeline = [{"$group": {"_id": "$priority", "count": {"$sum": 1}}}]
    category_pipeline = [{"$group": {"_id": "$category.name", "count": {"$sum": 1}}}]
    team_pipeline = [{"$group": {"_id": "$assignment.team", "count": {"$sum": 1}}}]

    by_status = {doc["_id"]: doc["count"] async for doc in db[c.INCIDENTS].aggregate(status_pipeline)}
    by_priority = {doc["_id"]: doc["count"] async for doc in db[c.INCIDENTS].aggregate(priority_pipeline)}
    by_category = {doc["_id"]: doc["count"] async for doc in db[c.INCIDENTS].aggregate(category_pipeline)}
    by_team = {doc["_id"]: doc["count"] async for doc in db[c.INCIDENTS].aggregate(team_pipeline)}

    resolved_pipeline = [
        {"$match": {"status": {"$in": ["resolved", "closed"]}, "resolution.resolved_at": {"$ne": None}}},
        {
            "$project": {
                "resolution_seconds": {
                    "$divide": [{"$subtract": ["$resolution.resolved_at", "$created_at"]}, 1000]
                }
            }
        },
        {"$group": {"_id": None, "avg_seconds": {"$avg": "$resolution_seconds"}, "count": {"$sum": 1}}},
    ]
    resolution_stats = [doc async for doc in db[c.INCIDENTS].aggregate(resolved_pipeline)]
    avg_resolution_seconds = resolution_stats[0]["avg_seconds"] if resolution_stats else None

    knowledge_count = await db[c.KNOWLEDGE_ARTICLES].count_documents({})
    ai_analyses_count = await db[c.AI_ANALYSES].count_documents({})

    return {
        "total_incidents": total_incidents,
        "by_status": by_status,
        "by_priority": by_priority,
        "by_category": by_category,
        "by_team": by_team,
        "avg_resolution_seconds": avg_resolution_seconds,
        "knowledge_article_count": knowledge_count,
        "ai_analyses_count": ai_analyses_count,
    }
