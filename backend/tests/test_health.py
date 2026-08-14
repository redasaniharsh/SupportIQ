import pytest

pytestmark = pytest.mark.asyncio


async def test_health_endpoint(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] in ("ok", "degraded")
    assert "ai_provider" in body
    assert body["ai_provider"] == "mock"
