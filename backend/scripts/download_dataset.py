#!/usr/bin/env python3
"""Downloads the mindweave/help-desk-tickets dataset from Hugging Face into
backend/data/raw/*.csv.

Paths are always project-root-relative via pathlib (never hardcoded
absolute paths), so this works regardless of where the repo is checked out.
"""
from __future__ import annotations

import sys
from pathlib import Path

# backend/scripts/download_dataset.py -> parents[1] = backend/, parents[2] = repo root
BACKEND_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = BACKEND_ROOT / "data" / "raw"

DATASET_ID = "mindweave/help-desk-tickets"
CONFIGS = ["agents", "categories", "comments", "tickets", "sla_breaches"]


def main() -> None:
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    try:
        from datasets import load_dataset
    except ImportError:
        print("ERROR: the 'datasets' package is required. Install via requirements.txt.", file=sys.stderr)
        sys.exit(1)

    any_succeeded = False
    for config_name in CONFIGS:
        out_path = RAW_DATA_DIR / f"{config_name}.csv"
        try:
            print(f"Loading config '{config_name}' from {DATASET_ID}...")
            ds = load_dataset(DATASET_ID, config_name)
            # Most HF datasets expose a single "train" split for tabular data.
            split_name = "train" if "train" in ds else list(ds.keys())[0]
            df = ds[split_name].to_pandas()
            df.to_csv(out_path, index=False)
            print(f"  -> wrote {len(df)} rows to {out_path}")
            any_succeeded = True
        except Exception as exc:
            print(f"  -> WARNING: could not load config '{config_name}': {exc}", file=sys.stderr)
            print(f"     (this config may not exist for this dataset revision; continuing)", file=sys.stderr)
            continue

    if not any_succeeded:
        print(
            "ERROR: none of the expected configs could be downloaded. Check network access, "
            "Hugging Face auth (HF_TOKEN), and the dataset id.",
            file=sys.stderr,
        )
        sys.exit(1)

    print("Done. Raw CSVs are in:", RAW_DATA_DIR)


if __name__ == "__main__":
    main()
