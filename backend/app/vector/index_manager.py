"""High-level index lifecycle management used by ingestion scripts."""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.utils.ids import chunk_id
from app.vector.metadata import build_metadata
from app.vector.pinecone_client import PineconeClientWrapper

logger = get_logger(__name__)

BATCH_SIZE = 96  # Pinecone integrated-embedding upsert batch limit is generous; keep conservative


async def ensure_ready(client: PineconeClientWrapper) -> bool:
    return await client.ensure_index()


def build_record(
    *,
    document_id: str,
    chunk_index: int,
    text: str,
    document_type: str,
    category: str | None,
    service: str | None,
    source: str,
    title: str,
    priority: str | None = None,
    has_resolution: bool = False,
) -> dict[str, Any]:
    """Builds a Pinecone `upsert_records` record: deterministic `_id` plus
    the integrated-embedding `text` field and small metadata fields (all
    flattened into the record itself, since upsert_records has a flat
    schema rather than a nested metadata dict)."""
    record_id = chunk_id(document_id, chunk_index)
    metadata = build_metadata(
        document_id=document_id,
        document_type=document_type,
        category=category,
        service=service,
        chunk_index=chunk_index,
        source=source,
        title=title,
        priority=priority,
        has_resolution=has_resolution,
    )
    record = {"_id": record_id, "text": text}
    record.update(metadata)
    return record


async def upsert_in_batches(
    client: PineconeClientWrapper,
    *,
    namespace: str,
    records: list[dict[str, Any]],
    batch_size: int = BATCH_SIZE,
    max_retries: int = 3,
) -> int:
    """Idempotent batched upsert (safe to rerun — deterministic _id means
    reruns overwrite, never duplicate). Retries transient failures."""
    total = 0
    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        attempt = 0
        while True:
            try:
                await client.upsert_records(namespace, batch)
                total += len(batch)
                break
            except Exception as exc:
                attempt += 1
                if attempt > max_retries:
                    logger.error("upsert_batch_failed_permanently", extra={"error": str(exc), "batch_start": i})
                    raise
                logger.warning("upsert_batch_retry", extra={"attempt": attempt, "error": str(exc)})
    return total
