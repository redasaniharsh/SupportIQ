"""Post-LLM guardrail pass.

- Strips any evidence_id in the LLM's structured response that does not
  actually exist in the retrieved-evidence set (never trust the model's
  citations blindly).
- Computes an independent `evidence_score` / confidence bucket (High /
  Medium / Low) from retrieval quality, never from the LLM's self-reported
  confidence alone.
"""
from __future__ import annotations

from app.ai.schemas import AIAnalysisResponse
from app.models.ai_analysis import ConfidenceInfo


def _valid_ids(response: AIAnalysisResponse, known_ids: set[str]) -> AIAnalysisResponse:
    data = response.model_dump()

    for cause in data["probable_causes"]:
        cause["evidence_ids"] = [e for e in cause["evidence_ids"] if e in known_ids]
    for action in data["recommended_actions"]:
        action["evidence_ids"] = [e for e in action["evidence_ids"] if e in known_ids]

    data["similar_incidents"] = [s for s in data["similar_incidents"] if s["evidence_id"] in known_ids]
    data["knowledge_articles"] = [k for k in data["knowledge_articles"] if k["evidence_id"] in known_ids]

    return AIAnalysisResponse(**data)


def sanitize_response(response: AIAnalysisResponse, evidence: list[dict]) -> AIAnalysisResponse:
    """Strip any evidence_id not present in the retrieved evidence set."""
    known_ids = {item["evidence_id"] for item in evidence}
    return _valid_ids(response, known_ids)


def compute_confidence(
    *,
    evidence: list[dict],
    response: AIAnalysisResponse,
    retrieval_count: int,
) -> ConfidenceInfo:
    """Independently computes a 0..1 evidence_score and a High/Medium/Low
    bucket from retrieval quality/count/agreement — never trusting the
    LLM's self-reported confidence as the primary signal.
    """
    if not evidence:
        evidence_score = 0.0
    else:
        avg_score = sum(item.get("score", 0.0) or 0.0 for item in evidence) / len(evidence)
        count_factor = min(len(evidence) / 5.0, 1.0)  # saturates at 5+ evidence items

        cited_ids: set[str] = set()
        for cause in response.probable_causes:
            cited_ids.update(cause.evidence_ids)
        for action in response.recommended_actions:
            cited_ids.update(action.evidence_ids)
        agreement_factor = min(len(cited_ids) / max(len(evidence), 1), 1.0)

        evidence_score = round(0.5 * avg_score + 0.3 * count_factor + 0.2 * agreement_factor, 4)
        evidence_score = max(0.0, min(1.0, evidence_score))

    if evidence_score >= 0.66:
        bucket = "High"
    elif evidence_score >= 0.35:
        bucket = "Medium"
    else:
        bucket = "Low"

    return ConfidenceInfo(
        model_reported=response.confidence,
        evidence_score=evidence_score,
        bucket=bucket,
    )
