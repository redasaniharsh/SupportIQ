import pytest

pytestmark = pytest.mark.asyncio


def _incident_payload(**overrides):
    payload = {
        "title": "VPN connection failure after password reset",
        "description": "User cannot connect to VPN after resetting their password this morning.",
        "category": {"id": 3, "name": "Network & VPN", "service": "network"},
        "priority": "P3",
    }
    payload.update(overrides)
    return payload


async def test_create_and_get_incident(client):
    resp = await client.post("/api/incidents", json=_incident_payload())
    assert resp.status_code == 201
    created = resp.json()
    assert created["incident_id"].startswith("INC-")
    assert created["status"] == "open"

    incident_id = created["incident_id"]
    get_resp = await client.get(f"/api/incidents/{incident_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["title"] == _incident_payload()["title"]


async def test_get_incident_not_found_returns_error_envelope(client):
    resp = await client.get("/api/incidents/INC-999999")
    assert resp.status_code == 404
    body = resp.json()
    assert body["error"]["code"] == "INCIDENT_NOT_FOUND"


async def test_list_incidents_pagination_defaults(client):
    for i in range(3):
        await client.post("/api/incidents", json=_incident_payload(title=f"Issue {i}"))

    resp = await client.get("/api/incidents")
    assert resp.status_code == 200
    body = resp.json()
    assert body["page"] == 1
    assert body["page_size"] == 20
    assert body["total"] >= 3
    assert len(body["items"]) >= 3


async def test_update_incident_status_valid_transition(client):
    create_resp = await client.post("/api/incidents", json=_incident_payload())
    incident_id = create_resp.json()["incident_id"]

    patch_resp = await client.patch(f"/api/incidents/{incident_id}", json={"status": "in_progress"})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "in_progress"


async def test_update_incident_invalid_transition_rejected(client):
    create_resp = await client.post("/api/incidents", json=_incident_payload())
    incident_id = create_resp.json()["incident_id"]

    # open -> closed directly is not an allowed forward transition
    patch_resp = await client.patch(f"/api/incidents/{incident_id}", json={"status": "closed"})
    assert patch_resp.status_code == 400
    assert patch_resp.json()["error"]["code"] == "INVALID_INCIDENT_TRANSITION"


async def test_resolve_requires_all_fields(client):
    create_resp = await client.post("/api/incidents", json=_incident_payload())
    incident_id = create_resp.json()["incident_id"]

    # Missing required fields should fail Pydantic validation (422)
    resp = await client.post(f"/api/incidents/{incident_id}/resolve", json={"root_cause": "x"})
    assert resp.status_code == 422


async def test_resolve_incident_success(client):
    create_resp = await client.post("/api/incidents", json=_incident_payload())
    incident_id = create_resp.json()["incident_id"]

    resolve_resp = await client.post(
        f"/api/incidents/{incident_id}/resolve",
        json={
            "root_cause": "Cached VPN credentials were stale after password reset.",
            "resolution_description": "Cleared cached credentials and reconnected with new password.",
            "resolved_by": "agent.jane",
        },
    )
    assert resolve_resp.status_code == 200
    body = resolve_resp.json()
    assert body["status"] == "resolved"
    assert body["resolution"]["root_cause"]
    assert body["resolution"]["resolved_by"] == "agent.jane"


async def test_delete_incident(client):
    create_resp = await client.post("/api/incidents", json=_incident_payload())
    incident_id = create_resp.json()["incident_id"]

    delete_resp = await client.delete(f"/api/incidents/{incident_id}")
    assert delete_resp.status_code == 204

    get_resp = await client.get(f"/api/incidents/{incident_id}")
    assert get_resp.status_code == 404


async def test_comments_flow(client):
    create_resp = await client.post("/api/incidents", json=_incident_payload())
    incident_id = create_resp.json()["incident_id"]

    comment_resp = await client.post(
        f"/api/incidents/{incident_id}/comments",
        json={"body": "Escalating to network team.", "author": "agent.jane"},
    )
    assert comment_resp.status_code == 201

    list_resp = await client.get(f"/api/incidents/{incident_id}/comments")
    assert list_resp.status_code == 200
    body = list_resp.json()
    assert body["total"] == 1
    assert body["items"][0]["body"] == "Escalating to network team."
