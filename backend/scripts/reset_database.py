#!/usr/bin/env python3
"""Drops the app's Mongo collections and optionally deletes the Pinecone
index/namespaces, for a clean re-run of the ingestion pipeline.

Usage:
    python scripts/reset_database.py             # Mongo only
    python scripts/reset_database.py --pinecone  # also clears Pinecone namespaces
    python scripts/reset_database.py --pinecone --drop-index  # deletes the whole index
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import get_settings  # noqa: E402
from app.core.logging import configure_logging  # noqa: E402
from app.db.collections import ALL_COLLECTIONS  # noqa: E402
from app.db.mongo import mongo_manager  # noqa: E402
from app.vector.metadata import NAMESPACE_HISTORICAL, NAMESPACE_KNOWLEDGE  # noqa: E402
from app.vector.pinecone_client import PineconeClientWrapper  # noqa: E402


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pinecone", action="store_true", help="Also clear Pinecone namespaces.")
    parser.add_argument("--drop-index", action="store_true", help="Delete the entire Pinecone index (implies --pinecone).")
    parser.add_argument("--yes", action="store_true", help="Skip the confirmation prompt.")
    args = parser.parse_args()

    if not args.yes:
        confirm = input("This will DROP all app Mongo collections. Type 'yes' to continue: ")
        if confirm.strip().lower() != "yes":
            print("Aborted.")
            return

    configure_logging("INFO")
    settings = get_settings()
    await mongo_manager.connect(settings)
    db = mongo_manager.db

    for name in ALL_COLLECTIONS:
        result = await db[name].delete_many({})
        print(f"Cleared collection '{name}': {result.deleted_count} documents removed.")

    if args.pinecone or args.drop_index:
        if not settings.pinecone_api_key:
            print("PINECONE_API_KEY not set — skipping Pinecone cleanup.")
        else:
            client = PineconeClientWrapper(settings)
            if args.drop_index:
                await client.delete_index()
                print(f"Deleted Pinecone index '{settings.pinecone_index_name}'.")
            else:
                await client.delete_namespace(NAMESPACE_KNOWLEDGE)
                await client.delete_namespace(NAMESPACE_HISTORICAL)
                print("Cleared Pinecone namespaces 'knowledge' and 'historical-tickets'.")

    await mongo_manager.close()
    print("Reset complete.")


if __name__ == "__main__":
    asyncio.run(main())
