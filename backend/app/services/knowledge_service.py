"""Knowledge article CRUD."""
from __future__ import annotations

from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import KnowledgeArticleNotFound
from app.db import collections as c
from app.utils.dates import utcnow
from app.utils.ids import format_knowledge_id
from app.utils.mongo_json import strip_id, strip_ids
from app.utils.pagination import build_page_envelope, clamp_pagination, compute_skip


async def _next_article_sequence(db: AsyncIOMotorDatabase) -> int:
    doc = await db[c.KNOWLEDGE_ARTICLES].find_one(sort=[("article_id", -1)])
    if not doc:
        return 1
    try:
        return int(doc["article_id"].split("-")[-1]) + 1
    except (ValueError, KeyError, IndexError):
        count = await db[c.KNOWLEDGE_ARTICLES].count_documents({})
        return count + 1


async def create_article(db: AsyncIOMotorDatabase, payload: dict[str, Any]) -> dict[str, Any]:
    sequence = await _next_article_sequence(db)
    article_id = format_knowledge_id(sequence)
    now = utcnow()
    doc = {
        **payload,
        "article_id": article_id,
        "version": payload.get("version", 1),
        "created_at": now,
        "updated_at": now,
    }
    await db[c.KNOWLEDGE_ARTICLES].insert_one(dict(doc))
    return doc


async def get_article(db: AsyncIOMotorDatabase, article_id: str) -> dict[str, Any]:
    doc = await db[c.KNOWLEDGE_ARTICLES].find_one({"article_id": article_id})
    if not doc:
        raise KnowledgeArticleNotFound(f"Knowledge article {article_id} was not found.")
    return strip_id(doc)


async def list_articles(
    db: AsyncIOMotorDatabase,
    *,
    filters: dict[str, Any],
    page: Optional[int],
    page_size: Optional[int],
) -> dict[str, Any]:
    page, page_size = clamp_pagination(page, page_size)
    query: dict[str, Any] = {}
    if filters.get("category"):
        query["category"] = filters["category"]
    if filters.get("service"):
        query["service"] = filters["service"]
    if filters.get("search"):
        query["$text"] = {"$search": filters["search"]}

    total = await db[c.KNOWLEDGE_ARTICLES].count_documents(query)
    cursor = (
        db[c.KNOWLEDGE_ARTICLES]
        .find(query)
        .sort("created_at", -1)
        .skip(compute_skip(page, page_size))
        .limit(page_size)
    )
    items = strip_ids([doc async for doc in cursor])
    return build_page_envelope(items, page=page, page_size=page_size, total=total)
