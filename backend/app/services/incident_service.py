"""Incident CRUD + lifecycle rules.

Rule-based validation only (state transitions, required resolution fields,
priority enum) — no keyword-based "AI" logic lives here, per the
assessment's constraints.
"""
from __future__ import annotations

from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import IncidentNotFound, InvalidIncidentTransition
from app.db import collections as c
from app.models.incident import IncidentStatus, is_valid_transition
from app.utils.dates import utcnow
from app.utils.ids import format_incident_id
from app.utils.mongo_json import strip_id, strip_ids
from app.utils.pagination import build_page_envelope, clamp_pagination, compute_skip


async def _next_incident_sequence(db: AsyncIOMotorDatabase) -> int:
    """Finds the highest existing incident sequence number and returns +1.

    Uses a simple max-scan on the indexed incident_id field; for a
    high-throughput production system this would use a dedicated counters
    collection with findAndModify, but for this assessment's scale a sorted
    query on an indexed field is sufficient and avoids a second moving part.
    """
    doc = await db[c.INCIDENTS].find_one(sort=[("incident_id", -1)])
    if not doc:
        return 1
    try:
        return int(doc["incident_id"].split("-")[-1]) + 1
    except (ValueError, KeyError, IndexError):
        count = await db[c.INCIDENTS].count_documents({})
        return count + 1


async def create_incident(db: AsyncIOMotorDatabase, payload: dict[str, Any]) -> dict[str, Any]:
    sequence = await _next_incident_sequence(db)
    incident_id = format_incident_id(sequence)
    # Guard against a rare race by retrying with a fresh sequence on duplicate key.
    now = utcnow()
    doc = {
        **payload,
        "incident_id": incident_id,
        "status": payload.get("status", IncidentStatus.OPEN.value),
        "ai": payload.get("ai") or {"last_analysis_id": None, "analyzed_at": None, "confidence": None},
        "resolution": payload.get("resolution")
        or {"root_cause": None, "description": None, "resolved_by": None, "resolved_at": None},
        "created_at": now,
        "updated_at": now,
    }
    for attempt in range(5):
        try:
            await db[c.INCIDENTS].insert_one(dict(doc))
            return doc
        except Exception as exc:  # duplicate key on incident_id race
            if "duplicate key" in str(exc).lower():
                sequence += 1
                doc["incident_id"] = format_incident_id(sequence)
                continue
            raise
    raise RuntimeError("Failed to allocate a unique incident_id after retries.")


async def get_incident(db: AsyncIOMotorDatabase, incident_id: str) -> dict[str, Any]:
    doc = await db[c.INCIDENTS].find_one({"incident_id": incident_id})
    if not doc:
        raise IncidentNotFound(f"Incident {incident_id} was not found.")
    return strip_id(doc)


async def list_incidents(
    db: AsyncIOMotorDatabase,
    *,
    filters: dict[str, Any],
    page: Optional[int],
    page_size: Optional[int],
) -> dict[str, Any]:
    page, page_size = clamp_pagination(page, page_size)
    query: dict[str, Any] = {}

    if filters.get("status"):
        query["status"] = filters["status"]
    if filters.get("priority"):
        query["priority"] = filters["priority"]
    if filters.get("category"):
        query["category.name"] = filters["category"]
    if filters.get("service"):
        query["category.service"] = filters["service"]
    if filters.get("team"):
        query["assignment.team"] = filters["team"]
    if filters.get("assignee_id"):
        query["assignment.assignee_id"] = filters["assignee_id"]

    date_range: dict[str, Any] = {}
    if filters.get("date_from"):
        date_range["$gte"] = filters["date_from"]
    if filters.get("date_to"):
        date_range["$lte"] = filters["date_to"]
    if date_range:
        query["created_at"] = date_range

    if filters.get("search"):
        query["$text"] = {"$search": filters["search"]}

    total = await db[c.INCIDENTS].count_documents(query)
    cursor = (
        db[c.INCIDENTS]
        .find(query)
        .sort("created_at", -1)
        .skip(compute_skip(page, page_size))
        .limit(page_size)
    )
    items = strip_ids([doc async for doc in cursor])
    return build_page_envelope(items, page=page, page_size=page_size, total=total)


async def update_incident(db: AsyncIOMotorDatabase, incident_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    current = await get_incident(db, incident_id)

    if "status" in updates and updates["status"] is not None:
        target_status = IncidentStatus(updates["status"])
        current_status = IncidentStatus(current["status"])
        if not is_valid_transition(current_status, target_status):
            raise InvalidIncidentTransition(
                f"Cannot transition incident {incident_id} from {current_status.value} to {target_status.value}. "
                "Use the reopen action for backward transitions from closed."
            )

    updates = {k: v for k, v in updates.items() if v is not None}
    if not updates:
        return current

    updates["updated_at"] = utcnow()
    await db[c.INCIDENTS].update_one({"incident_id": incident_id}, {"$set": updates})
    return await get_incident(db, incident_id)


async def delete_incident(db: AsyncIOMotorDatabase, incident_id: str) -> None:
    result = await db[c.INCIDENTS].delete_one({"incident_id": incident_id})
    if result.deleted_count == 0:
        raise IncidentNotFound(f"Incident {incident_id} was not found.")
    await db[c.COMMENTS].delete_many({"incident_id": incident_id})


async def reopen_incident(db: AsyncIOMotorDatabase, incident_id: str, target_status: str, reason: Optional[str]) -> dict[str, Any]:
    current = await get_incident(db, incident_id)
    current_status = IncidentStatus(current["status"])
    if current_status != IncidentStatus.CLOSED:
        raise InvalidIncidentTransition(f"Incident {incident_id} is not closed; use PATCH to change status instead.")

    await db[c.INCIDENTS].update_one(
        {"incident_id": incident_id},
        {"$set": {"status": target_status, "updated_at": utcnow()}},
    )
    if reason:
        from app.utils.ids import new_analysis_id  # local import to avoid cycle at module load

        await db[c.AUDIT_EVENTS].insert_one(
            {
                "event_id": new_analysis_id(),
                "incident_id": incident_id,
                "event_type": "reopen",
                "reason": reason,
                "created_at": utcnow(),
            }
        )
    return await get_incident(db, incident_id)
