"""Tests for the /analyze and /similar endpoints using the mock LLM client
and a stubbed retrieval pipeline (no real Pinecone/LLM network calls)."""
from __future__ import annotations

import pytest

from app.services import ai_service

pytestmark = pytest.mark.asyncio


class FakePipeline:
    """Stubs out Pinecone-backed retrieval with fixed evidence."""

    async def retrieve_evidence(self, incident):
        return {
            "knowledge_evidence": [
                {
                    "evidence_id": "KB-006::chunk-000",
                    "document_id": "KB-006",
                    "document_type": "knowledge",
                    "text": "VPN connection fails after password reset because cached credentials are stale.",
                    "title": "VPN Connection Fails or Drops Repeatedly",
                    "source": "knowledge_articles",
                    "score": 0.88,
                }
            ],
            "historical_evidence": [
                {
                    "evidence_id": "INC-000042::chunk-000",
                    "document_id": "INC-000042",
                    "document_type": "historical-tickets",
                    "text": "Similar VPN failure resolved by clearing cached credentials.",
                    "title": "VPN failure after reset",
                    "source": "incidents",
                    "score": 0.81,
                }
            ],
            "retrieval_count": 2,
        }

    async def find_similar_incidents(self, incident, exclude_incident_id=None, top_k=10):
        return [
            {"incident_id": "INC-000042", "title": "VPN failure after reset", "similarity": 0.93, "relationship": "duplicate"},
            {"incident_id": "INC-000099", "title": "Related VPN issue", "similarity": 0.80, "relationship": "related"},
        ]


def _incident_payload():
    return {
        "title": "VPN connection failure after password reset",
        "description": "User cannot connect to VPN after resetting their password this morning.",
        "category": {"id": 3, "name": "Network & VPN", "service": "network"},
        "priority": "P3",
    }


async def test_analyze_returns_ok_with_mock_llm_and_stub_retrieval(client, monkeypatch):
    monkeypatch.setattr(ai_service, "get_retrieval_pipeline", lambda settings=None: FakePipeline())

    create_resp = await client.post("/api/incidents", json=_incident_payload())
    incident_id = create_resp.json()["incident_id"]

    resp = await client.post(f"/api/incidents/{incident_id}/analyze")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["retrieval_count"] == 2
    assert body["analysis"]["summary"]
    assert body["confidence"]["bucket"] in ("High", "Medium", "Low")
    # guardrail: every cited evidence_id must be one of the retrieved ones
    known_ids = {"KB-006::chunk-000", "INC-000042::chunk-000"}
    for cause in body["analysis"]["probable_causes"]:
        assert set(cause["evidence_ids"]).issubset(known_ids)


async def test_analyze_returns_ai_unavailable_on_retrieval_failure(client, monkeypatch):
    class FailingPipeline:
        async def retrieve_evidence(self, incident):
            from app.core.exceptions import RetrievalError

            raise RetrievalError("Pinecone is unreachable in this test.")

    monkeypatch.setattr(ai_service, "get_retrieval_pipeline", lambda settings=None: FailingPipeline())

    create_resp = await client.post("/api/incidents", json=_incident_payload())
    incident_id = create_resp.json()["incident_id"]

    resp = await client.post(f"/api/incidents/{incident_id}/analyze")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ai_unavailable"
    assert body["retryable"] is True


async def test_analyze_returns_ai_unavailable_on_llm_failure(client, monkeypatch):
    monkeypatch.setattr(ai_service, "get_retrieval_pipeline", lambda settings=None: FakePipeline())

    from app.ai.llm_client import BaseLLMClient
    from app.core.exceptions import AIServiceError

    class FailingLLMClient(BaseLLMClient):
        async def complete_json(self, *, system_prompt, user_prompt):
            raise AIServiceError("The model timed out.")

    monkeypatch.setattr(ai_service, "get_llm_client", lambda settings: FailingLLMClient())

    create_resp = await client.post("/api/incidents", json=_incident_payload())
    incident_id = create_resp.json()["incident_id"]

    resp = await client.post(f"/api/incidents/{incident_id}/analyze")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ai_unavailable"
    assert body["retryable"] is True


async def test_similar_incidents_endpoint(client, monkeypatch):
    from app.services import similarity_service

    monkeypatch.setattr(similarity_service, "get_retrieval_pipeline", lambda settings=None: FakePipeline())

    create_resp = await client.post("/api/incidents", json=_incident_payload())
    incident_id = create_resp.json()["incident_id"]

    resp = await client.get(f"/api/incidents/{incident_id}/similar")
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"][0]["relationship"] == "duplicate"
    assert body["items"][1]["relationship"] == "related"
