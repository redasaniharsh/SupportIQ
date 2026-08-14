"""Shared pytest fixtures.

Uses mongomock-motor to fake AsyncIOMotorClient so tests never require a
real MongoDB instance, and forces AI_PROVIDER=mock so no real LLM/Pinecone
credentials are needed either.
"""
from __future__ import annotations

import os

# Set dummy env vars before any app module reads settings.
os.environ.setdefault("AI_PROVIDER", "mock")
os.environ.setdefault("LLM_PROVIDER", "mock")
os.environ.setdefault("LLM_API_KEY", "test-dummy-key")
os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017")
os.environ.setdefault("MONGODB_DATABASE", "ai_service_desk_test")
os.environ.setdefault("PINECONE_API_KEY", "test-dummy-pinecone-key")
os.environ.setdefault("FRONTEND_URL", "http://localhost:5173")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient

from app.db import indexes as indexes_module
from app.db.mongo import mongo_manager


@pytest_asyncio.fixture
async def fake_db():
    """A fresh in-memory Mongo database per test, wired into the singleton
    mongo_manager the same way the real app lifespan does."""
    client = AsyncMongoMockClient()
    db = client["ai_service_desk_test"]

    mongo_manager._client = client
    mongo_manager._db = db

    try:
        await indexes_module.create_indexes(db)
    except Exception:
        # mongomock does not support every index option (e.g. text indexes
        # fully) — safe to ignore for unit tests that don't rely on them.
        pass

    yield db

    mongo_manager._client = None
    mongo_manager._db = None


@pytest_asyncio.fixture
async def app(fake_db):
    from app.main import create_app

    application = create_app()
    yield application


@pytest_asyncio.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
