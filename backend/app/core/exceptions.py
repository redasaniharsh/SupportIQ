"""Domain exceptions and FastAPI exception handlers.

All errors returned to clients use the consistent envelope:
    {"error": {"code": "SOME_CODE", "message": "human readable message"}}
"""
from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.logging import get_logger

logger = get_logger(__name__)


class AppError(Exception):
    """Base class for all domain-level errors."""

    code = "APP_ERROR"
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, message: str, *, code: str | None = None, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        if status_code:
            self.status_code = status_code


class IncidentNotFound(AppError):
    code = "INCIDENT_NOT_FOUND"
    status_code = status.HTTP_404_NOT_FOUND


class InvalidIncidentTransition(AppError):
    code = "INVALID_INCIDENT_TRANSITION"
    status_code = status.HTTP_400_BAD_REQUEST


class AIServiceError(AppError):
    code = "AI_SERVICE_ERROR"
    status_code = status.HTTP_502_BAD_GATEWAY


class RetrievalError(AppError):
    code = "RETRIEVAL_ERROR"
    status_code = status.HTTP_502_BAD_GATEWAY


class DatabaseError(AppError):
    code = "DATABASE_ERROR"
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


class KnowledgeArticleNotFound(AppError):
    code = "KNOWLEDGE_ARTICLE_NOT_FOUND"
    status_code = status.HTTP_404_NOT_FOUND


class ValidationFailed(AppError):
    code = "VALIDATION_FAILED"
    status_code = 422


def _error_body(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        logger.warning("app_error", extra={"code": exc.code, "path": str(request.url)})
        return JSONResponse(status_code=exc.status_code, content=_error_body(exc.code, exc.message))

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_body("REQUEST_VALIDATION_ERROR", str(exc.errors())),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("unhandled_exception", extra={"path": str(request.url)})
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_body("INTERNAL_SERVER_ERROR", "An unexpected error occurred."),
        )
