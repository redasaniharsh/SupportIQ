"""FastAPI application entrypoint: lifespan for Mongo connect/close, CORS
from ALLOWED_ORIGINS / FRONTEND_URL, router includes."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import ai, comments, dashboard, incidents, knowledge, search
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.db.indexes import create_indexes
from app.db.mongo import mongo_manager

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await mongo_manager.connect(settings)
    try:
        await create_indexes(mongo_manager.db)
    except Exception as exc:  # pragma: no cover - index creation failures shouldn't block boot
        logger.warning("index_creation_failed", extra={"error": str(exc)})
    logger.info("app_startup_complete")
    yield
    await mongo_manager.close()
    logger.info("app_shutdown_complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Service Desk API",
        description="Support incident management with RAG-based AI analysis.",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Build allowed origins from ALLOWED_ORIGINS (comma-separated) with
    # FRONTEND_URL as a fallback so local dev still works out of the box.
    raw = settings.allowed_origins.strip()
    if raw:
        origins = [o.strip().rstrip("/") for o in raw.split(",") if o.strip()]
    else:
        origins = [settings.frontend_url.rstrip("/")]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    app.include_router(incidents.router)
    app.include_router(comments.router)
    app.include_router(ai.router)
    app.include_router(knowledge.router)
    app.include_router(dashboard.router)
    app.include_router(search.router)

    @app.get("/api/health")
    async def health():
        mongo_ok = await mongo_manager.ping()
        return {
            "status": "ok" if mongo_ok else "degraded",
            "mongo_connected": mongo_ok,
            "ai_provider": settings.ai_provider,
        }

    return app


app = create_app()
