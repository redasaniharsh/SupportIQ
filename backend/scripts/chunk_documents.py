#!/usr/bin/env python3
"""Semantic-aware chunking per DESIGN.md section 6.1.

Reads knowledge_articles and incidents (+ comments) from Mongo, produces
chunk records, and writes them as JSON lines to data/processed/ for the
indexing script to pick up. Deterministic chunk IDs (KB-001::chunk-000,
INC-000123::chunk-000) make reruns idempotent.
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import get_settings  # noqa: E402
from app.core.logging import configure_logging, get_logger  # noqa: E402
from app.db import collections as c  # noqa: E402
from app.db.mongo import mongo_manager  # noqa: E402
from app.utils.ids import chunk_id  # noqa: E402
from app.utils.text import chunk_text_by_tokens, filter_noise_comments, normalize_whitespace  # noqa: E402

PROCESSED_DIR = BACKEND_ROOT / "data" / "processed"
logger = get_logger(__name__)

KB_TARGET_TOKENS = 400
KB_OVERLAP_TOKENS = 65
TICKET_TARGET_TOKENS = 475
TICKET_OVERLAP_TOKENS = 75


def _kb_prefix(article: dict[str, Any], section: str) -> str:
    return f"{article['title']} / {article['category']} / {section} / Symptoms: {'; '.join(article.get('symptoms', []))}\n"


def chunk_knowledge_article(article: dict[str, Any]) -> list[dict[str, Any]]:
    """Section-aware chunking: never splits mid-step. Each logical section
    (symptoms+causes, troubleshooting steps, resolution+escalation) becomes
    its own token-bounded chunk group, each prefixed with article context so
    it is self-contained when retrieved in isolation."""
    document_id = article["article_id"]
    sections: list[tuple[str, str]] = []

    overview = "Symptoms: " + "; ".join(article.get("symptoms", [])) + ". Root causes: " + "; ".join(
        article.get("root_causes", [])
    )
    sections.append(("Overview", overview))

    steps_text = " ".join(f"Step {i + 1}: {s}" for i, s in enumerate(article.get("troubleshooting_steps", [])))
    if steps_text:
        sections.append(("Troubleshooting Steps", steps_text))

    resolution_text = "Resolution: " + article.get("resolution", "")
    if article.get("escalation_conditions"):
        resolution_text += " Escalate if: " + "; ".join(article["escalation_conditions"])
    sections.append(("Resolution & Escalation", resolution_text))

    chunks = []
    chunk_index = 0
    for section_name, section_text in sections:
        prefix = _kb_prefix(article, section_name)
        full_text = normalize_whitespace(prefix + section_text)
        for sub_chunk in chunk_text_by_tokens(full_text, target_tokens=KB_TARGET_TOKENS, overlap_tokens=KB_OVERLAP_TOKENS):
            chunks.append(
                {
                    "chunk_id": chunk_id(document_id, chunk_index),
                    "document_id": document_id,
                    "document_type": "knowledge",
                    "category": article["category"],
                    "service": article.get("service"),
                    "chunk_index": chunk_index,
                    "source": "knowledge_articles",
                    "title": article["title"],
                    "has_resolution": True,
                    "text": sub_chunk,
                }
            )
            chunk_index += 1
    return chunks


def build_ticket_document_text(incident: dict[str, Any], comments: list[dict[str, Any]]) -> str:
    category = incident.get("category", {}) or {}
    parts = [
        f"Title: {incident.get('title', '')}",
        f"Description: {incident.get('description', '')}",
        f"Category: {category.get('name', 'Unknown')}",
        f"Service: {category.get('service', 'unknown')}",
        f"Priority: {incident.get('priority', 'P3')}",
    ]
    resolution = incident.get("resolution") or {}
    if resolution.get("description"):
        parts.append(f"Resolution: {resolution['description']}")
    if resolution.get("root_cause"):
        parts.append(f"Root cause: {resolution['root_cause']}")

    comment_bodies = [comment.get("body", "") for comment in comments]
    useful_comments = filter_noise_comments(comment_bodies)
    if useful_comments:
        parts.append("Comments: " + " | ".join(useful_comments))

    return normalize_whitespace(" ".join(parts))


def chunk_ticket(incident: dict[str, Any], comments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    document_id = incident["incident_id"]
    category = incident.get("category", {}) or {}
    full_text = build_ticket_document_text(incident, comments)

    sub_chunks = chunk_text_by_tokens(full_text, target_tokens=TICKET_TARGET_TOKENS, overlap_tokens=TICKET_OVERLAP_TOKENS)
    has_resolution = bool((incident.get("resolution") or {}).get("description"))

    chunks = []
    for chunk_index, sub_chunk in enumerate(sub_chunks):
        chunks.append(
            {
                "chunk_id": chunk_id(document_id, chunk_index),
                "document_id": document_id,
                "document_type": "historical-tickets",
                "category": category.get("name"),
                "service": category.get("service"),
                "priority": incident.get("priority"),
                "chunk_index": chunk_index,
                "source": "incidents",
                "title": incident.get("title", ""),
                "has_resolution": has_resolution,
                "text": sub_chunk,
            }
        )
    return chunks


async def main() -> None:
    configure_logging("INFO")
    settings = get_settings()
    await mongo_manager.connect(settings)
    db = mongo_manager.db

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    knowledge_chunks: list[dict[str, Any]] = []
    async for article in db[c.KNOWLEDGE_ARTICLES].find({}):
        article.pop("_id", None)
        knowledge_chunks.extend(chunk_knowledge_article(article))

    ticket_chunks: list[dict[str, Any]] = []
    async for incident in db[c.INCIDENTS].find({}):
        incident.pop("_id", None)
        comments = [doc async for doc in db[c.COMMENTS].find({"incident_id": incident["incident_id"]})]
        for comment in comments:
            comment.pop("_id", None)
        ticket_chunks.extend(chunk_ticket(incident, comments))

    kb_out = PROCESSED_DIR / "knowledge_chunks.jsonl"
    with kb_out.open("w", encoding="utf-8") as f:
        for chunk in knowledge_chunks:
            f.write(json.dumps(chunk, default=str) + "\n")

    ticket_out = PROCESSED_DIR / "ticket_chunks.jsonl"
    with ticket_out.open("w", encoding="utf-8") as f:
        for chunk in ticket_chunks:
            f.write(json.dumps(chunk, default=str) + "\n")

    print(f"Wrote {len(knowledge_chunks)} knowledge chunks to {kb_out}")
    print(f"Wrote {len(ticket_chunks)} ticket chunks to {ticket_out}")

    await mongo_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
