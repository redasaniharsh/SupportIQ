#!/usr/bin/env python3
"""Validates Pinecone credentials, creates the index if missing, and
batches + upserts chunks from data/processed/*.jsonl with deterministic IDs
(idempotent — safe to rerun). Retries transient failures and logs an
ingestion_runs update.
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import get_settings  # noqa: E402
from app.core.logging import configure_logging, get_logger  # noqa: E402
from app.core.exceptions import RetrievalError  # noqa: E402
from app.db import collections as c  # noqa: E402
from app.db.mongo import mongo_manager  # noqa: E402
from app.utils.dates import utcnow  # noqa: E402
from app.utils.ids import new_ingestion_run_id  # noqa: E402
from app.vector.index_manager import upsert_in_batches  # noqa: E402
from app.vector.metadata import NAMESPACE_HISTORICAL, NAMESPACE_KNOWLEDGE  # noqa: E402
from app.vector.pinecone_client import PineconeClientWrapper  # noqa: E402

PROCESSED_DIR = BACKEND_ROOT / "data" / "processed"
logger = get_logger(__name__)


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _to_record(chunk: dict) -> dict:
    record = {"_id": chunk["chunk_id"], "text": chunk["text"]}
    for key in ("document_id", "document_type", "category", "service", "priority", "chunk_index", "source", "title", "has_resolution"):
        if key in chunk and chunk[key] is not None:
            record[key] = chunk[key]
    return record


async def main() -> None:
    configure_logging("INFO")
    settings = get_settings()

    if not settings.pinecone_api_key:
        print("ERROR: PINECONE_API_KEY is not set. Aborting.", file=sys.stderr)
        sys.exit(1)

    await mongo_manager.connect(settings)
    db = mongo_manager.db

    run_id = new_ingestion_run_id()
    started_at = utcnow()
    summary = {"run_id": run_id, "started_at": started_at, "stage": "index_pinecone"}

    client = PineconeClientWrapper(settings)

    try:
        created = await client.ensure_index()
        print(f"Index '{settings.pinecone_index_name}' {'created' if created else 'already exists'}.")

        knowledge_chunks = [_to_record(c_) for c_ in _load_jsonl(PROCESSED_DIR / "knowledge_chunks.jsonl")]
        ticket_chunks = [_to_record(c_) for c_ in _load_jsonl(PROCESSED_DIR / "ticket_chunks.jsonl")]

        if not knowledge_chunks and not ticket_chunks:
            print("No processed chunks found. Run chunk_documents.py first.", file=sys.stderr)

        kb_upserted = 0
        if knowledge_chunks:
            kb_upserted = await upsert_in_batches(client, namespace=NAMESPACE_KNOWLEDGE, records=knowledge_chunks)
            print(f"Upserted {kb_upserted} knowledge vectors into namespace '{NAMESPACE_KNOWLEDGE}'.")

        ticket_upserted = 0
        if ticket_chunks:
            ticket_upserted = await upsert_in_batches(client, namespace=NAMESPACE_HISTORICAL, records=ticket_chunks)
            print(f"Upserted {ticket_upserted} ticket vectors into namespace '{NAMESPACE_HISTORICAL}'.")

        summary.update(
            {
                "status": "success",
                "vectors_upserted": kb_upserted + ticket_upserted,
                "knowledge_vectors": kb_upserted,
                "ticket_vectors": ticket_upserted,
                "finished_at": utcnow(),
            }
        )
    except Exception as exc:
        summary.update({"status": "failed", "error": str(exc), "finished_at": utcnow()})
        logger.exception("index_pinecone_failed")
        raise
    finally:
        await db[c.INGESTION_RUNS].insert_one(dict(summary))
        await mongo_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
