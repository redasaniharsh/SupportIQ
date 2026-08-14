#!/usr/bin/env python3
"""Normalizes raw dataset CSVs into the canonical incident schema
(DESIGN.md section 5.1) and imports agents/categories/comments into Mongo.

Original fields are preserved under `source_data` on every imported
document. Writes an `ingestion_runs` record summarizing the run.

Column names are looked up flexibly (case-insensitive, several aliases)
since the exact CSV headers are not assumed ahead of time — always run
inspect_dataset.py first to confirm the real schema for your dataset
revision.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any, Optional

import pandas as pd

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import get_settings  # noqa: E402
from app.core.logging import configure_logging, get_logger  # noqa: E402
from app.db import collections as c  # noqa: E402
from app.db.indexes import create_indexes  # noqa: E402
from app.db.mongo import mongo_manager  # noqa: E402
from app.models.incident import IncidentStatus, Priority  # noqa: E402
from app.utils.dates import utcnow  # noqa: E402
from app.utils.ids import format_incident_id, new_ingestion_run_id  # noqa: E402

RAW_DATA_DIR = BACKEND_ROOT / "data" / "raw"
logger = get_logger(__name__)

STATUS_MAP = {
    "open": IncidentStatus.OPEN,
    "new": IncidentStatus.OPEN,
    "in progress": IncidentStatus.IN_PROGRESS,
    "in_progress": IncidentStatus.IN_PROGRESS,
    "pending": IncidentStatus.PENDING,
    "on hold": IncidentStatus.PENDING,
    "resolved": IncidentStatus.RESOLVED,
    "closed": IncidentStatus.CLOSED,
}

PRIORITY_MAP = {
    "p1": Priority.P1,
    "critical": Priority.P1,
    "urgent": Priority.P1,
    "p2": Priority.P2,
    "high": Priority.P2,
    "p3": Priority.P3,
    "medium": Priority.P3,
    "normal": Priority.P3,
    "p4": Priority.P4,
    "low": Priority.P4,
}


def _col(df: pd.DataFrame, *candidates: str) -> Optional[str]:
    lower_cols = {col.lower().strip(): col for col in df.columns}
    for candidate in candidates:
        if candidate in lower_cols:
            return lower_cols[candidate]
    return None


def _load_csv(name: str) -> Optional[pd.DataFrame]:
    path = RAW_DATA_DIR / f"{name}.csv"
    if not path.exists():
        logger.warning(f"missing_csv: {path}")
        return None
    return pd.read_csv(path)


def _map_status(value: Any) -> str:
    if pd.isna(value):
        return IncidentStatus.OPEN.value
    key = str(value).strip().lower()
    return STATUS_MAP.get(key, IncidentStatus.OPEN).value


def _map_priority(value: Any) -> str:
    if pd.isna(value):
        return Priority.P3.value
    key = str(value).strip().lower()
    return PRIORITY_MAP.get(key, Priority.P3).value


def _row_to_dict(row: pd.Series) -> dict[str, Any]:
    return {k: (None if pd.isna(v) else v) for k, v in row.to_dict().items()}


async def import_categories(db, df: pd.DataFrame) -> int:
    id_col = _col(df, "category_id", "id")
    name_col = _col(df, "name", "category", "category_name")
    service_col = _col(df, "service", "team")
    count = 0
    for _, row in df.iterrows():
        doc = {
            "category_id": int(row[id_col]) if id_col and not pd.isna(row[id_col]) else count,
            "name": str(row[name_col]) if name_col else "Unknown",
            "service": str(row[service_col]) if service_col and not pd.isna(row[service_col]) else None,
            "source_data": _row_to_dict(row),
        }
        await db[c.CATEGORIES].update_one({"category_id": doc["category_id"]}, {"$set": doc}, upsert=True)
        count += 1
    return count


async def import_agents(db, df: pd.DataFrame) -> int:
    id_col = _col(df, "agent_id", "id")
    name_col = _col(df, "name", "agent_name", "full_name")
    email_col = _col(df, "email")
    team_col = _col(df, "team", "department")
    role_col = _col(df, "role", "title")
    count = 0
    for _, row in df.iterrows():
        agent_id = str(row[id_col]) if id_col and not pd.isna(row[id_col]) else f"AGT-{count}"
        doc = {
            "agent_id": agent_id,
            "name": str(row[name_col]) if name_col and not pd.isna(row[name_col]) else "Unknown Agent",
            "email": str(row[email_col]) if email_col and not pd.isna(row[email_col]) else None,
            "team": str(row[team_col]) if team_col and not pd.isna(row[team_col]) else None,
            "role": str(row[role_col]) if role_col and not pd.isna(row[role_col]) else None,
            "source_data": _row_to_dict(row),
        }
        await db[c.AGENTS].update_one({"agent_id": agent_id}, {"$set": doc}, upsert=True)
        count += 1
    return count


def _load_category_lookup() -> dict[int, dict[str, Optional[str]]]:
    """Builds a category_id -> {name, service} map from categories.csv.

    tickets.csv only carries a numeric `category_id` foreign key, not the
    category's human-readable name or its service/team — those live in
    categories.csv. Ticket rows resolve their display category and default
    team through this lookup rather than assuming tickets.csv duplicates
    that data inline.
    """
    categories_df = _load_csv("categories")
    lookup: dict[int, dict[str, Optional[str]]] = {}
    if categories_df is None:
        return lookup
    id_col = _col(categories_df, "category_id", "id")
    name_col = _col(categories_df, "name", "category", "category_name")
    service_col = _col(categories_df, "service", "team")
    if not id_col:
        return lookup
    for _, row in categories_df.iterrows():
        if pd.isna(row[id_col]):
            continue
        lookup[int(row[id_col])] = {
            "name": str(row[name_col]) if name_col and not pd.isna(row[name_col]) else "Unknown",
            "service": str(row[service_col]) if service_col and not pd.isna(row[service_col]) else None,
        }
    return lookup


async def import_tickets(db, df: pd.DataFrame) -> tuple[int, dict[str, str]]:
    """Returns (count_imported, record_id -> incident_id map) for comment linking."""
    category_lookup = _load_category_lookup()

    record_id_col = _col(df, "ticket_id", "id")
    title_col = _col(df, "title", "subject", "summary")
    desc_col = _col(df, "description", "body", "details")
    status_col = _col(df, "status")
    priority_col = _col(df, "priority")
    category_col = _col(df, "category", "category_name")
    category_id_col = _col(df, "category_id")
    service_col = _col(df, "service", "affected_service")
    team_col = _col(df, "team", "assigned_team")
    assignee_col = _col(df, "assignee_id", "agent_id", "assigned_agent_id")
    root_cause_col = _col(df, "root_cause")
    resolution_col = _col(df, "resolution", "resolution_description")
    resolved_by_col = _col(df, "resolved_by")
    created_col = _col(df, "created_at", "created", "date_created")

    record_map: dict[str, str] = {}
    count = 0
    for idx, row in df.iterrows():
        sequence = count + 1
        incident_id = format_incident_id(sequence)
        record_id = str(row[record_id_col]) if record_id_col and not pd.isna(row[record_id_col]) else str(idx)

        title = str(row[title_col]) if title_col and not pd.isna(row[title_col]) else "Untitled ticket"
        description = str(row[desc_col]) if desc_col and not pd.isna(row[desc_col]) else ""

        status_value = _map_status(row[status_col]) if status_col else IncidentStatus.OPEN.value
        priority_value = _map_priority(row[priority_col]) if priority_col else Priority.P3.value

        category_id = int(row[category_id_col]) if category_id_col and not pd.isna(row[category_id_col]) else None
        cat_info = category_lookup.get(category_id, {}) if category_id is not None else {}

        category_name = (
            str(row[category_col])
            if category_col and not pd.isna(row[category_col])
            else cat_info.get("name", "Uncategorized")
        )
        service = (
            str(row[service_col])
            if service_col and not pd.isna(row[service_col])
            else cat_info.get("service")
        )

        resolution = {
            "root_cause": str(row[root_cause_col]) if root_cause_col and not pd.isna(row.get(root_cause_col)) else None,
            "description": str(row[resolution_col]) if resolution_col and not pd.isna(row.get(resolution_col)) else None,
            "resolved_by": str(row[resolved_by_col]) if resolved_by_col and not pd.isna(row.get(resolved_by_col)) else None,
            "resolved_at": None,
        }
        if status_value in (IncidentStatus.RESOLVED.value, IncidentStatus.CLOSED.value) and resolution["description"]:
            resolution["resolved_at"] = utcnow()

        now = utcnow()
        doc = {
            "incident_id": incident_id,
            "title": title[:300],
            "description": description,
            "status": status_value,
            "priority": priority_value,
            "category": {"id": category_id, "name": category_name, "service": service},
            "assignment": {
                "team": str(row[team_col]) if team_col and not pd.isna(row.get(team_col)) else service,
                "assignee_id": str(row[assignee_col]) if assignee_col and not pd.isna(row.get(assignee_col)) else None,
            },
            "source": {"type": "dataset", "dataset": "mindweave/help-desk-tickets", "record_id": record_id},
            "ai": {"last_analysis_id": None, "analyzed_at": None, "confidence": None},
            "resolution": resolution,
            "source_data": _row_to_dict(row),
            "created_at": now,
            "updated_at": now,
        }
        await db[c.INCIDENTS].update_one({"source.record_id": record_id}, {"$set": doc}, upsert=True)
        record_map[record_id] = incident_id
        count += 1

    return count, record_map


async def import_comments(db, df: pd.DataFrame, record_map: dict[str, str]) -> int:
    fk_col = _col(df, "ticket_id", "incident_id")
    id_col = _col(df, "comment_id", "id")
    body_col = _col(df, "body", "comment", "text", "message")
    author_col = _col(df, "author", "agent_name", "created_by")
    created_col = _col(df, "created_at", "created", "date")

    count = 0
    for idx, row in df.iterrows():
        record_id = str(row[fk_col]) if fk_col and not pd.isna(row[fk_col]) else None
        incident_id = record_map.get(record_id)
        if not incident_id:
            continue  # orphaned comment row with no matching ticket
        comment_id = str(row[id_col]) if id_col and not pd.isna(row[id_col]) else f"CMT-{idx}"
        doc = {
            "comment_id": comment_id,
            "incident_id": incident_id,
            "author": str(row[author_col]) if author_col and not pd.isna(row.get(author_col)) else None,
            "author_id": None,
            "body": str(row[body_col]) if body_col and not pd.isna(row.get(body_col)) else "",
            "is_internal": False,
            "source_data": _row_to_dict(row),
            "created_at": utcnow(),
        }
        await db[c.COMMENTS].update_one({"comment_id": comment_id}, {"$set": doc}, upsert=True)
        count += 1
    return count


async def main() -> None:
    configure_logging("INFO")
    settings = get_settings()
    await mongo_manager.connect(settings)
    db = mongo_manager.db
    await create_indexes(db)

    run_id = new_ingestion_run_id()
    started_at = utcnow()
    summary: dict[str, Any] = {"run_id": run_id, "started_at": started_at, "stage": "import_dataset"}

    try:
        categories_df = _load_csv("categories")
        agents_df = _load_csv("agents")
        tickets_df = _load_csv("tickets")
        comments_df = _load_csv("comments")

        categories_count = await import_categories(db, categories_df) if categories_df is not None else 0
        agents_count = await import_agents(db, agents_df) if agents_df is not None else 0

        if tickets_df is not None:
            incidents_count, record_map = await import_tickets(db, tickets_df)
        else:
            incidents_count, record_map = 0, {}

        comments_count = await import_comments(db, comments_df, record_map) if comments_df is not None else 0

        summary.update(
            {
                "status": "success",
                "categories_imported": categories_count,
                "agents_imported": agents_count,
                "incidents_imported": incidents_count,
                "comments_imported": comments_count,
                "finished_at": utcnow(),
            }
        )
        print(
            f"Imported: {categories_count} categories, {agents_count} agents, "
            f"{incidents_count} incidents, {comments_count} comments."
        )
    except Exception as exc:
        summary.update({"status": "failed", "error": str(exc), "finished_at": utcnow()})
        logger.exception("import_dataset_failed")
        raise
    finally:
        await db[c.INGESTION_RUNS].insert_one(dict(summary))
        await mongo_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
