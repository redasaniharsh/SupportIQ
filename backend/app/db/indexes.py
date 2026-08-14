"""Creates all Mongo indexes described in DESIGN.md section 5."""
from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.logging import get_logger
from app.db import collections as c

logger = get_logger(__name__)


async def create_indexes(db: AsyncIOMotorDatabase) -> None:
    # incidents
    await db[c.INCIDENTS].create_index("incident_id", unique=True, name="uniq_incident_id")
    await db[c.INCIDENTS].create_index([("status", 1), ("created_at", -1)], name="status_created_at")
    await db[c.INCIDENTS].create_index([("priority", 1), ("created_at", -1)], name="priority_created_at")
    await db[c.INCIDENTS].create_index([("category.name", 1), ("created_at", -1)], name="category_created_at")
    await db[c.INCIDENTS].create_index([("assignment.team", 1), ("created_at", -1)], name="team_created_at")
    await db[c.INCIDENTS].create_index("source.record_id", name="source_record_id")
    await db[c.INCIDENTS].create_index(
        [("title", "text"), ("description", "text")], name="incident_text_search"
    )

    # comments
    await db[c.COMMENTS].create_index([("incident_id", 1), ("created_at", 1)], name="incident_created_at")

    # knowledge_articles
    await db[c.KNOWLEDGE_ARTICLES].create_index("article_id", unique=True, name="uniq_article_id")
    await db[c.KNOWLEDGE_ARTICLES].create_index("category", name="kb_category")
    await db[c.KNOWLEDGE_ARTICLES].create_index(
        [("title", "text"), ("symptoms", "text"), ("resolution", "text")], name="kb_text_search"
    )

    # ai_analyses
    await db[c.AI_ANALYSES].create_index("analysis_id", unique=True, name="uniq_analysis_id")
    await db[c.AI_ANALYSES].create_index([("incident_id", 1), ("created_at", -1)], name="incident_created_at_ai")

    # agents / categories
    await db[c.AGENTS].create_index("agent_id", unique=True, name="uniq_agent_id")
    await db[c.CATEGORIES].create_index("category_id", unique=True, name="uniq_category_id")

    # audit_events
    await db[c.AUDIT_EVENTS].create_index([("incident_id", 1), ("created_at", -1)], name="audit_incident_created_at")

    # ingestion_runs
    await db[c.INGESTION_RUNS].create_index([("started_at", -1)], name="ingestion_started_at")

    logger.info("indexes_created")
