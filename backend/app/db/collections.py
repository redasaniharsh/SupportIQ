"""Collection name constants and getters."""
from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase

INCIDENTS = "incidents"
COMMENTS = "comments"
AGENTS = "agents"
CATEGORIES = "categories"
KNOWLEDGE_ARTICLES = "knowledge_articles"
AI_ANALYSES = "ai_analyses"
AUDIT_EVENTS = "audit_events"
INGESTION_RUNS = "ingestion_runs"

ALL_COLLECTIONS = (
    INCIDENTS,
    COMMENTS,
    AGENTS,
    CATEGORIES,
    KNOWLEDGE_ARTICLES,
    AI_ANALYSES,
    AUDIT_EVENTS,
    INGESTION_RUNS,
)


def get_collection(db: AsyncIOMotorDatabase, name: str) -> AsyncIOMotorCollection:
    return db[name]


def incidents(db: AsyncIOMotorDatabase) -> AsyncIOMotorCollection:
    return db[INCIDENTS]


def comments(db: AsyncIOMotorDatabase) -> AsyncIOMotorCollection:
    return db[COMMENTS]


def agents(db: AsyncIOMotorDatabase) -> AsyncIOMotorCollection:
    return db[AGENTS]


def categories(db: AsyncIOMotorDatabase) -> AsyncIOMotorCollection:
    return db[CATEGORIES]


def knowledge_articles(db: AsyncIOMotorDatabase) -> AsyncIOMotorCollection:
    return db[KNOWLEDGE_ARTICLES]


def ai_analyses(db: AsyncIOMotorDatabase) -> AsyncIOMotorCollection:
    return db[AI_ANALYSES]


def audit_events(db: AsyncIOMotorDatabase) -> AsyncIOMotorCollection:
    return db[AUDIT_EVENTS]


def ingestion_runs(db: AsyncIOMotorDatabase) -> AsyncIOMotorCollection:
    return db[INGESTION_RUNS]
