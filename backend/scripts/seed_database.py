#!/usr/bin/env python3
"""One-shot: clears MongoDB (and optionally Pinecone), then re-imports the
raw dataset CSVs into their respective Mongo collections.

This combines what reset_database.py and import_dataset.py already do into
a single run, so you don't need two separate commands. It reuses the exact
same column-mapping / import functions as import_dataset.py (imported
below) rather than duplicating that logic.

Usage:
    python scripts/seed_database.py                       # clears Mongo only, then imports
    python scripts/seed_database.py --pinecone             # also clears Pinecone namespaces
    python scripts/seed_database.py --pinecone --drop-index  # also deletes the whole Pinecone index
    python scripts/seed_database.py --yes                  # skip the confirmation prompt

Run from anywhere (repo root or backend/) — app.core.config now anchors
.env to backend/.env regardless of the current working directory, so this
always talks to the same database no matter where you invoke it from.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = SCRIPTS_DIR.parent
sys.path.insert(0, str(BACKEND_ROOT))
sys.path.insert(0, str(SCRIPTS_DIR))

from app.core.config import get_settings  # noqa: E402
from app.core.logging import configure_logging, get_logger  # noqa: E402
from app.db import collections as c  # noqa: E402
from app.db.collections import ALL_COLLECTIONS  # noqa: E402
from app.db.indexes import create_indexes  # noqa: E402
from app.db.mongo import mongo_manager  # noqa: E402
from app.utils.dates import utcnow  # noqa: E402
from app.utils.ids import new_ingestion_run_id  # noqa: E402
from app.vector.metadata import NAMESPACE_HISTORICAL, NAMESPACE_KNOWLEDGE  # noqa: E402
from app.vector.pinecone_client import PineconeClientWrapper  # noqa: E402

# Reuse the exact same import logic as import_dataset.py — no duplicated
# column-mapping code to drift out of sync.
from import_dataset import (  # noqa: E402
    RAW_DATA_DIR,
    _load_csv,
    import_agents,
    import_categories,
    import_comments,
    import_tickets,
)

logger = get_logger(__name__)


async def clear_mongo(db) -> None:
    for name in ALL_COLLECTIONS:
        result = await db[name].delete_many({})
        print(f"  Cleared collection '{name}': {result.deleted_count} documents removed.")


async def clear_pinecone(settings, *, drop_index: bool) -> None:
    if not settings.pinecone_api_key:
        print("  PINECONE_API_KEY not set — skipping Pinecone cleanup.")
        return
    client = PineconeClientWrapper(settings)
    if drop_index:
        await client.delete_index()
        print(f"  Deleted Pinecone index '{settings.pinecone_index_name}'.")
    else:
        await client.delete_namespace(NAMESPACE_KNOWLEDGE)
        await client.delete_namespace(NAMESPACE_HISTORICAL)
        print("  Cleared Pinecone namespaces 'knowledge' and 'historical-tickets'.")


async def seed_mongo(db) -> dict[str, int]:
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

    return {
        "categories_imported": categories_count,
        "agents_imported": agents_count,
        "incidents_imported": incidents_count,
        "comments_imported": comments_count,
    }


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pinecone", action="store_true", help="Also clear Pinecone namespaces.")
    parser.add_argument(
        "--drop-index", action="store_true", help="Delete the entire Pinecone index (implies --pinecone)."
    )
    parser.add_argument("--yes", action="store_true", help="Skip the confirmation prompt.")
    args = parser.parse_args()

    if not args.yes:
        confirm = input(
            "This will DROP all app Mongo collections"
            + (" and clear Pinecone" if (args.pinecone or args.drop_index) else "")
            + ", then re-import the CSVs in backend/data/raw/. Type 'yes' to continue: "
        )
        if confirm.strip().lower() != "yes":
            print("Aborted.")
            return

    if not RAW_DATA_DIR.exists() or not any(RAW_DATA_DIR.glob("*.csv")):
        print(f"No CSVs found in {RAW_DATA_DIR}. Run download_dataset.py first.")
        return

    configure_logging("INFO")
    settings = get_settings()
    await mongo_manager.connect(settings)
    db = mongo_manager.db

    run_id = new_ingestion_run_id()
    started_at = utcnow()
    summary: dict = {"run_id": run_id, "started_at": started_at, "stage": "seed_database"}

    try:
        print("Clearing MongoDB collections...")
        await clear_mongo(db)

        if args.pinecone or args.drop_index:
            print("Clearing Pinecone...")
            await clear_pinecone(settings, drop_index=args.drop_index)

        await create_indexes(db)

        print("Re-importing dataset CSVs into MongoDB...")
        counts = await seed_mongo(db)
        summary.update({"status": "success", **counts, "finished_at": utcnow()})

        print(
            "Imported: "
            f"{counts['categories_imported']} categories, "
            f"{counts['agents_imported']} agents, "
            f"{counts['incidents_imported']} incidents, "
            f"{counts['comments_imported']} comments."
        )
        print(
            "\nNote: this only reseeds MongoDB. To (re)populate Pinecone vectors, run:\n"
            "  python scripts/build_knowledge_base.py\n"
            "  python scripts/chunk_documents.py\n"
            "  python scripts/index_pinecone.py\n"
            "  python scripts/verify_ingestion.py"
        )
    except Exception as exc:
        summary.update({"status": "failed", "error": str(exc), "finished_at": utcnow()})
        logger.exception("seed_database_failed")
        raise
    finally:
        await db[c.INGESTION_RUNS].insert_one(dict(summary))
        await mongo_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
