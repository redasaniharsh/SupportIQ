"""Motor AsyncIOMotorClient singleton and connect/close/ping helpers.

The client is created once during the FastAPI lifespan and reused for every
request via a dependency — never created per-request.
"""
from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import Settings, get_settings
from app.core.exceptions import DatabaseError
from app.core.logging import get_logger

logger = get_logger(__name__)


class MongoManager:
    """Holds the single AsyncIOMotorClient instance for the app lifetime."""

    def __init__(self) -> None:
        self._client: AsyncIOMotorClient | None = None
        self._db: AsyncIOMotorDatabase | None = None

    async def connect(self, settings: Settings | None = None) -> None:
        settings = settings or get_settings()
        if self._client is not None:
            return
        self._client = AsyncIOMotorClient(settings.mongodb_uri, uuidRepresentation="standard")
        self._db = self._client[settings.mongodb_database]
        logger.info("mongo_connect", extra={"database": settings.mongodb_database})

    async def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("mongo_close")

    async def ping(self) -> bool:
        if self._client is None:
            return False
        try:
            await self._client.admin.command("ping")
            return True
        except Exception as exc:  # pragma: no cover - network dependent
            logger.error("mongo_ping_failed", extra={"error": str(exc)})
            return False

    @property
    def db(self) -> AsyncIOMotorDatabase:
        if self._db is None:
            raise DatabaseError("Database connection has not been initialized.")
        return self._db

    @property
    def client(self) -> AsyncIOMotorClient:
        if self._client is None:
            raise DatabaseError("Mongo client has not been initialized.")
        return self._client

    @property
    def is_connected(self) -> bool:
        return self._client is not None


# Module-level singleton used across the application.
mongo_manager = MongoManager()


def get_database() -> AsyncIOMotorDatabase:
    """FastAPI dependency returning the singleton database handle."""
    return mongo_manager.db
