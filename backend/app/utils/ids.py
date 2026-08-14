"""ID generation helpers.

Incident IDs look like INC-000001 (zero-padded, sequential).
Knowledge article IDs look like KB-001.
Chunk IDs are deterministic: "<DOCUMENT_ID>::chunk-<NNN>".
Analysis IDs are UUID4-based (they aren't referenced by external evidence
tags, so randomness is fine there).
"""
from __future__ import annotations

import hashlib
import uuid

INCIDENT_PREFIX = "INC"
KNOWLEDGE_PREFIX = "KB"


def format_incident_id(sequence: int) -> str:
    return f"{INCIDENT_PREFIX}-{sequence:06d}"


def format_knowledge_id(sequence: int) -> str:
    return f"{KNOWLEDGE_PREFIX}-{sequence:03d}"


def chunk_id(document_id: str, index: int) -> str:
    """Deterministic chunk id: DOCUMENT_ID::chunk-NNN (zero-padded to 3)."""
    return f"{document_id}::chunk-{index:03d}"


def content_hash(text: str) -> str:
    """Stable sha256 hash of text content, used for idempotent dedupe keys."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def new_analysis_id() -> str:
    return f"AN-{uuid.uuid4().hex[:16]}"


def new_ingestion_run_id() -> str:
    return f"RUN-{uuid.uuid4().hex[:12]}"
