"""AI analysis orchestration service — the core RAG loop from DESIGN.md 2/6.

Incident creation never depends on this succeeding. On any AI/LLM/retrieval
failure this returns a structured "ai_unavailable" result rather than
raising, so callers (the /analyze endpoint) can surface it cleanly.
"""
from __future__ import annotations

import time
from typing import Any, Optional

import pydantic
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.ai.guardrails import compute_confidence, sanitize_response
from app.ai.llm_client import BaseLLMClient, build_prompts, get_llm_client
from app.ai.schemas import AIAnalysisResponse
from app.core.config import Settings, get_settings
from app.core.exceptions import AIServiceError, RetrievalError
from app.core.logging import get_logger
from app.db import collections as c
from app.models.ai_analysis import PROMPT_VERSION
from app.services.retrieval_service import get_retrieval_pipeline
from app.utils.dates import utcnow
from app.utils.ids import new_analysis_id
from app.vector.retriever import RetrievalPipeline

logger = get_logger(__name__)


async def run_analysis(
    db: AsyncIOMotorDatabase,
    incident: dict[str, Any],
    *,
    llm_client: Optional[BaseLLMClient] = None,
    pipeline: Optional[RetrievalPipeline] = None,
    settings: Optional[Settings] = None,
) -> dict[str, Any]:
    """Returns either:
      {"status": "ok", ...full analysis payload...}
    or:
      {"status": "ai_unavailable", "message": str, "retryable": True}
    Never raises for AI/retrieval failures.
    """
    settings = settings or get_settings()
    started = time.monotonic()

    try:
        pipeline = pipeline or get_retrieval_pipeline(settings=settings)
        evidence_bundle = await pipeline.retrieve_evidence(incident)
    except RetrievalError as exc:
        logger.warning("analysis_retrieval_failed", extra={"incident_id": incident.get("incident_id"), "error": str(exc)})
        return {"status": "ai_unavailable", "message": f"Evidence retrieval failed: {exc.message}", "retryable": True}
    except Exception as exc:  # pragma: no cover - defensive catch-all
        logger.exception("analysis_retrieval_unexpected_error")
        return {"status": "ai_unavailable", "message": f"Unexpected retrieval error: {exc}", "retryable": True}

    knowledge_evidence = evidence_bundle["knowledge_evidence"]
    historical_evidence = evidence_bundle["historical_evidence"]
    all_evidence = knowledge_evidence + historical_evidence

    try:
        llm_client = llm_client or get_llm_client(settings)
        system_prompt, user_prompt = build_prompts(
            incident=incident, knowledge_evidence=knowledge_evidence, historical_evidence=historical_evidence
        )
        raw_response = await llm_client.complete_json(system_prompt=system_prompt, user_prompt=user_prompt)
        parsed = AIAnalysisResponse(**raw_response)
    except AIServiceError as exc:
        logger.warning("analysis_llm_failed", extra={"incident_id": incident.get("incident_id"), "error": str(exc)})
        return {"status": "ai_unavailable", "message": exc.message, "retryable": True}
    except pydantic.ValidationError as exc:
        logger.warning("analysis_schema_invalid", extra={"incident_id": incident.get("incident_id"), "error": str(exc)})
        return {
            "status": "ai_unavailable",
            "message": "The AI response did not match the required schema.",
            "retryable": True,
        }
    except Exception as exc:  # pragma: no cover - defensive catch-all
        logger.exception("analysis_llm_unexpected_error")
        return {"status": "ai_unavailable", "message": f"Unexpected AI error: {exc}", "retryable": True}

    sanitized = sanitize_response(parsed, all_evidence)
    confidence = compute_confidence(evidence=all_evidence, response=sanitized, retrieval_count=len(all_evidence))

    latency_ms = int((time.monotonic() - started) * 1000)
    analysis_id = new_analysis_id()
    now = utcnow()

    evidence_refs = [
        {
            "evidence_id": item["evidence_id"],
            "document_type": item["document_type"],
            "document_id": item["document_id"],
            "title": item.get("title"),
            "score": item.get("score"),
            "source": item.get("source"),
        }
        for item in all_evidence
    ]

    record = {
        "analysis_id": analysis_id,
        "incident_id": incident["incident_id"],
        "prompt_version": PROMPT_VERSION,
        "model": getattr(llm_client, "_model", settings.llm_model) if not settings.is_mock_ai else "mock-llm",
        "response": sanitized.model_dump(),
        "evidence": evidence_refs,
        "confidence": confidence.model_dump(),
        "retrieval_count": len(all_evidence),
        "latency_ms": latency_ms,
        "created_at": now,
    }

    try:
        await db[c.AI_ANALYSES].insert_one(dict(record))
        await db[c.INCIDENTS].update_one(
            {"incident_id": incident["incident_id"]},
            {
                "$set": {
                    "ai.last_analysis_id": analysis_id,
                    "ai.analyzed_at": now,
                    "ai.confidence": confidence.bucket,
                    "updated_at": now,
                }
            },
        )
    except Exception:  # pragma: no cover - persistence issues shouldn't hide a good analysis
        logger.exception("analysis_persist_failed")

    return {
        "status": "ok",
        "analysis_id": analysis_id,
        "incident_id": incident["incident_id"],
        "model": record["model"],
        "prompt_version": PROMPT_VERSION,
        "analysis": sanitized.model_dump(),
        "evidence": evidence_refs,
        "confidence": confidence.model_dump(),
        "retrieval_count": len(all_evidence),
        "latency_ms": latency_ms,
        "created_at": now,
    }
