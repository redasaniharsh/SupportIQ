"""Knowledge base endpoints."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongo import get_database
from app.schemas.knowledge import KnowledgeCreateRequest
from app.services import knowledge_service

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.get("")
async def list_knowledge(
    category: Optional[str] = Query(None),
    service: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    filters = {"category": category, "service": service, "search": search}
    return await knowledge_service.list_articles(db, filters=filters, page=page, page_size=page_size)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_knowledge_article(payload: KnowledgeCreateRequest, db: AsyncIOMotorDatabase = Depends(get_database)):
    return await knowledge_service.create_article(db, payload.model_dump(mode="json"))


@router.get("/{article_id}")
async def get_knowledge_article(article_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    return await knowledge_service.get_article(db, article_id)
