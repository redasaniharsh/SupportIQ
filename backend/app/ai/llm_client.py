"""LLM client abstraction.

Real client: GroqLLMClient uses the official `groq` SDK (async) with the
GROQ_API_KEY / LLM_API_KEY from settings — never hardcoded.
Groq's API is OpenAI-compatible so the interface is identical.

Mock client: same interface, returns a deterministic, structurally valid
AIAnalysisResponse. Used when AI_PROVIDER=mock or LLM_PROVIDER=mock (tests /
offline dev only) — explicitly NOT real AI.
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

from app.ai.prompts import SYSTEM_PROMPT, build_user_prompt
from app.core.config import Settings
from app.core.exceptions import AIServiceError
from app.core.logging import get_logger

logger = get_logger(__name__)


class BaseLLMClient(ABC):
    @abstractmethod
    async def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """Returns a parsed JSON dict from the LLM's structured response."""
        raise NotImplementedError


class GroqLLMClient(BaseLLMClient):
    """Real client using the official Groq Python SDK (async).

    Groq's API is OpenAI-compatible. We use the `groq` package directly for
    first-class support and type safety.
    """

    def __init__(self, settings: Settings):
        try:
            from groq import AsyncGroq
        except ImportError as exc:  # pragma: no cover
            raise AIServiceError(
                "The 'groq' package is required. Install it with: pip install groq"
            ) from exc

        if not settings.llm_api_key:
            raise AIServiceError(
                "LLM_API_KEY is not configured; set GROQ_API_KEY / LLM_API_KEY in .env or use AI_PROVIDER=mock."
            )

        self._client = AsyncGroq(api_key=settings.llm_api_key)
        self._model = settings.llm_model

    async def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        try:
            completion = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt + "\n\nYou MUST respond with valid JSON only. No markdown, no prose — pure JSON."},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                max_tokens=4096,
            )
        except Exception as exc:  # network / auth / rate-limit / timeout, etc.
            logger.error("groq_call_failed", extra={"error": str(exc)})
            raise AIServiceError(f"Groq LLM call failed: {exc}") from exc

        try:
            content = completion.choices[0].message.content
            # Strip markdown code fences if the model wraps in ```json ... ```
            if content and content.strip().startswith("```"):
                content = content.strip().lstrip("`").lstrip("json").strip().rstrip("`").strip()
            return json.loads(content)
        except (IndexError, AttributeError, json.JSONDecodeError, TypeError) as exc:
            raise AIServiceError(f"Groq returned an unparsable response: {exc}") from exc


class MockLLMClient(BaseLLMClient):
    """Deterministic mock used for tests / offline dev. Clearly NOT real AI.

    Produces a structurally valid AIAnalysisResponse payload derived from
    whatever evidence_ids happen to be embedded in the user_prompt, so
    guardrail logic can be exercised meaningfully in tests.
    """

    async def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        evidence_ids = self._extract_evidence_ids(user_prompt)
        first_two = evidence_ids[:2]

        return {
            "summary": (
                "[MOCK AI - not real analysis] This is a deterministic placeholder "
                "summary generated because AI_PROVIDER=mock is set."
            ),
            "category": "Unclassified",
            "priority": "P3",
            "probable_causes": (
                [{"cause": "Mock probable cause based on retrieved evidence.", "evidence_ids": first_two, "likelihood": "Medium"}]
                if first_two
                else []
            ),
            "recommended_actions": [
                {
                    "action": "Review the incident manually; this is a mock AI response.",
                    "evidence_ids": first_two,
                    "priority_order": 1,
                }
            ],
            "similar_incidents": [],
            "knowledge_articles": [],
            "escalation_required": False,
            "confidence": "Low",
            "uncertainties": ["This analysis was produced by the mock LLM client and is not real AI output."],
            "final_recommendation": (
                "This is a mock response for testing/offline dev only. Configure LLM_API_KEY and "
                "set AI_PROVIDER=groq for real analysis."
            ),
        }

    @staticmethod
    def _extract_evidence_ids(user_prompt: str) -> list[str]:
        ids = []
        for line in user_prompt.splitlines():
            line = line.strip()
            if line.startswith("- evidence_id="):
                try:
                    ids.append(line.split("evidence_id=", 1)[1].split(" ", 1)[0])
                except IndexError:
                    continue
        return ids


def get_llm_client(settings: Settings) -> BaseLLMClient:
    if settings.is_mock_ai:
        logger.info("llm_client_mock_selected")
        return MockLLMClient()
    logger.info("llm_client_groq_selected", extra={"model": settings.llm_model})
    return GroqLLMClient(settings)


def build_prompts(*, incident: dict, knowledge_evidence: list[dict], historical_evidence: list[dict]) -> tuple[str, str]:
    user_prompt = build_user_prompt(
        incident=incident,
        knowledge_evidence=knowledge_evidence,
        historical_evidence=historical_evidence,
    )
    return SYSTEM_PROMPT, user_prompt
