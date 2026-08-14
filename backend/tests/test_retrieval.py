"""Unit tests for guardrails, reranker, chunking, and the retrieval
pipeline's fallback broadening/dedupe logic, with Pinecone fully mocked."""
from __future__ import annotations

import pytest

from app.ai.guardrails import compute_confidence, sanitize_response
from app.ai.reranker import rerank
from app.ai.schemas import AIAnalysisResponse
from app.utils.text import chunk_text_by_tokens, filter_noise_comments, is_noise_comment
from app.vector.retriever import RetrievalPipeline


def _sample_response(**overrides):
    base = dict(
        summary="VPN failure likely due to stale cached credentials.",
        category="Network & VPN",
        priority="P3",
        probable_causes=[
            {"cause": "Stale cached VPN credentials.", "evidence_ids": ["KB-006::chunk-000", "FAKE-999::chunk-000"], "likelihood": "High"}
        ],
        recommended_actions=[
            {"action": "Clear cached credentials and reconnect.", "evidence_ids": ["KB-006::chunk-000"], "priority_order": 1}
        ],
        similar_incidents=[{"incident_id": "INC-000042", "evidence_id": "FAKE-ID", "relationship": "duplicate", "rationale": None}],
        knowledge_articles=[{"article_id": "KB-006", "evidence_id": "KB-006::chunk-000", "relevance": "direct match"}],
        escalation_required=False,
        confidence="High",
        uncertainties=[],
        final_recommendation="Clear cached credentials and retry.",
    )
    base.update(overrides)
    return AIAnalysisResponse(**base)


def test_guardrail_strips_unknown_evidence_ids():
    evidence = [{"evidence_id": "KB-006::chunk-000", "score": 0.9}]
    response = _sample_response()

    sanitized = sanitize_response(response, evidence)

    assert sanitized.probable_causes[0].evidence_ids == ["KB-006::chunk-000"]
    assert sanitized.similar_incidents == []  # FAKE-ID stripped entirely


def test_confidence_is_computed_independently_of_llm_self_report():
    evidence = [{"evidence_id": "KB-006::chunk-000", "score": 0.9}, {"evidence_id": "INC-1::chunk-000", "score": 0.85}]
    response = _sample_response(confidence="Low")  # model says Low
    sanitized = sanitize_response(response, evidence)

    confidence = compute_confidence(evidence=evidence, response=sanitized, retrieval_count=2)

    assert confidence.model_reported == "Low"
    # Backend's own bucket is independent and reflects good evidence quality/count.
    assert confidence.bucket in ("High", "Medium", "Low")
    assert 0.0 <= confidence.evidence_score <= 1.0


def test_confidence_zero_when_no_evidence():
    response = _sample_response(probable_causes=[], recommended_actions=[], similar_incidents=[], knowledge_articles=[])
    confidence = compute_confidence(evidence=[], response=response, retrieval_count=0)
    assert confidence.evidence_score == 0.0
    assert confidence.bucket == "Low"


def test_reranker_prefers_category_match_and_lexical_overlap():
    candidates = [
        {"id": "A", "score": 0.7, "metadata": {"category": "Network & VPN"}, "text": "vpn connection failure password reset"},
        {"id": "B", "score": 0.72, "metadata": {"category": "Printers & Devices"}, "text": "printer offline queue stuck"},
    ]
    ranked = rerank(candidates, query_text="vpn connection failure password reset", category="Network & VPN")
    assert ranked[0]["id"] == "A"  # despite slightly lower semantic score, category+lexical match wins


def test_chunk_text_by_tokens_respects_target_and_overlap():
    text = " ".join([f"Sentence number {i} about VPN troubleshooting steps." for i in range(40)])
    chunks = chunk_text_by_tokens(text, target_tokens=100, overlap_tokens=20)
    assert len(chunks) > 1
    assert all(chunk.strip() for chunk in chunks)


def test_noise_comment_filtering():
    comments = ["thanks", "Ok", "Cleared the cached credentials and confirmed VPN connects now.", "done"]
    filtered = filter_noise_comments(comments)
    assert filtered == ["Cleared the cached credentials and confirmed VPN connects now."]
    assert is_noise_comment("thanks")
    assert not is_noise_comment("Cleared the cached credentials and confirmed VPN connects now.")


class FakePineconeClient:
    """Simulates Pinecone's search() for fallback-broadening tests."""

    def __init__(self, responses_by_filter):
        self.responses_by_filter = responses_by_filter
        self.calls = []

    async def search(self, *, namespace, query_text, top_k=10, filter=None):
        self.calls.append(filter)
        key = "with_filter" if filter else "no_filter"
        return self.responses_by_filter.get(key, [])


async def test_retrieval_pipeline_falls_back_when_filtered_results_are_thin():
    thin_results = [{"id": "KB-001::chunk-000", "score": 0.5, "text": "one result", "metadata": {"document_id": "KB-001", "category": "X"}}]
    broad_results = [
        {"id": f"KB-00{i}::chunk-000", "score": 0.6, "text": "result", "metadata": {"document_id": f"KB-00{i}", "category": "Y"}}
        for i in range(5)
    ]
    fake_client = FakePineconeClient({"with_filter": thin_results, "no_filter": broad_results})
    pipeline = RetrievalPipeline(client=fake_client)

    incident = {
        "incident_id": "INC-000001",
        "title": "Test incident",
        "description": "Some issue",
        "category": {"name": "Unmatched Category", "service": "unknown"},
    }
    result = await pipeline.retrieve_evidence(incident)

    # Should have broadened past the thin filtered result set.
    assert result["retrieval_count"] >= 5
    assert any(f is None for f in fake_client.calls)  # eventually tried an unfiltered search


async def test_similar_incidents_bucketed_by_threshold():
    from app.core.config import Settings

    settings = Settings(SIMILARITY_DUPLICATE_THRESHOLD=0.9, SIMILARITY_RELATED_THRESHOLD=0.75, LLM_API_KEY="x")
    results = [
        {"id": "INC-1::chunk-000", "score": 0.95, "text": "", "metadata": {"document_id": "INC-1", "title": "dup"}},
        {"id": "INC-2::chunk-000", "score": 0.80, "text": "", "metadata": {"document_id": "INC-2", "title": "related"}},
        {"id": "INC-3::chunk-000", "score": 0.50, "text": "", "metadata": {"document_id": "INC-3", "title": "unrelated"}},
    ]

    class FakeClient:
        async def search(self, *, namespace, query_text, top_k=10, filter=None):
            return results

    pipeline = RetrievalPipeline(client=FakeClient(), settings=settings)
    similar = await pipeline.find_similar_incidents({"incident_id": "INC-0", "title": "t", "description": "d", "category": {}})

    relationships = {item["incident_id"]: item["relationship"] for item in similar}
    assert relationships["INC-1"] == "duplicate"
    assert relationships["INC-2"] == "related"
    assert "INC-3" not in relationships  # below related threshold: not shown
