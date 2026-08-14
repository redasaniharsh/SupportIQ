#!/usr/bin/env python3
"""Checks Mongo counts, Pinecone namespace/vector counts, runs a real
semantic query, and prints a clean pass/fail report.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import get_settings  # noqa: E402
from app.core.logging import configure_logging  # noqa: E402
from app.db import collections as c  # noqa: E402
from app.db.mongo import mongo_manager  # noqa: E402
from app.vector.metadata import NAMESPACE_HISTORICAL, NAMESPACE_KNOWLEDGE  # noqa: E402
from app.vector.pinecone_client import PineconeClientWrapper  # noqa: E402

PASS = "✅"
FAIL = "❌"


async def main() -> None:
    configure_logging("INFO")
    settings = get_settings()
    await mongo_manager.connect(settings)
    db = mongo_manager.db

    print("=" * 60)
    print("AI Service Desk — Ingestion Verification Report")
    print("=" * 60)

    mongo_ok = await mongo_manager.ping()
    print(f"{PASS if mongo_ok else FAIL} MongoDB connection")

    counts = {}
    for name in (c.INCIDENTS, c.COMMENTS, c.AGENTS, c.CATEGORIES, c.KNOWLEDGE_ARTICLES, c.AI_ANALYSES, c.INGESTION_RUNS):
        counts[name] = await db[name].count_documents({})
        status = PASS if counts[name] > 0 else FAIL
        print(f"{status} Mongo collection '{name}': {counts[name]} documents")

    if not settings.pinecone_api_key:
        print(f"{FAIL} PINECONE_API_KEY not set — skipping Pinecone checks.")
    else:
        client = PineconeClientWrapper(settings)
        try:
            stats = await client.describe_index_stats()
            namespaces = stats.get("namespaces", {}) if isinstance(stats, dict) else {}
            kb_count = namespaces.get(NAMESPACE_KNOWLEDGE, {}).get("vector_count", 0)
            hist_count = namespaces.get(NAMESPACE_HISTORICAL, {}).get("vector_count", 0)
            print(f"{PASS if kb_count > 0 else FAIL} Pinecone namespace '{NAMESPACE_KNOWLEDGE}': {kb_count} vectors")
            print(f"{PASS if hist_count > 0 else FAIL} Pinecone namespace '{NAMESPACE_HISTORICAL}': {hist_count} vectors")

            sample_results = await client.search(
                namespace=NAMESPACE_KNOWLEDGE, query_text="VPN connection keeps failing after password reset", top_k=3
            )
            if sample_results:
                print(f"{PASS} Semantic query returned {len(sample_results)} result(s):")
                for r in sample_results:
                    print(f"    - {r['id']} (score={r['score']:.4f}) {r['metadata'].get('title', '')}")
            else:
                print(f"{FAIL} Semantic query returned no results.")
        except Exception as exc:
            print(f"{FAIL} Pinecone check failed: {exc}")

    print("=" * 60)
    await mongo_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
