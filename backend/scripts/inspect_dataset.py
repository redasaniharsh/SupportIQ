#!/usr/bin/env python3
"""Inspects the raw CSVs downloaded by download_dataset.py: row counts,
columns, nulls, duplicate IDs, FK relationships, samples, unique
categories/teams, priority/status distributions.

Reads actual CSV headers rather than assuming column names.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

BACKEND_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = BACKEND_ROOT / "data" / "raw"


def _load(name: str) -> pd.DataFrame | None:
    path = RAW_DATA_DIR / f"{name}.csv"
    if not path.exists():
        print(f"[skip] {name}.csv not found at {path}")
        return None
    return pd.read_csv(path)


def _find_id_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    lower_cols = {col.lower(): col for col in df.columns}
    for candidate in candidates:
        if candidate in lower_cols:
            return lower_cols[candidate]
    # fall back to any column ending in "_id" or exactly "id"
    for col in df.columns:
        if col.lower() == "id" or col.lower().endswith("_id"):
            return col
    return None


def inspect_frame(name: str, df: pd.DataFrame) -> None:
    print(f"\n{'=' * 70}\n{name.upper()}  ({len(df)} rows, {len(df.columns)} columns)\n{'=' * 70}")
    print("Columns:", list(df.columns))
    print("\nNull counts:")
    print(df.isnull().sum().to_string())

    id_col = _find_id_column(df, [f"{name[:-1]}_id", "id", "ticket_id"])
    if id_col:
        dup_count = df[id_col].duplicated().sum()
        print(f"\nID column detected: '{id_col}' — duplicate values: {dup_count}")

    print("\nSample rows:")
    print(df.head(3).to_string())

    for col in df.columns:
        lower = col.lower()
        if lower in ("category", "categories", "team", "priority", "status", "service"):
            print(f"\nUnique values for '{col}' ({df[col].nunique()} unique):")
            print(df[col].value_counts(dropna=False).head(20).to_string())


def main() -> None:
    print(f"Inspecting raw dataset CSVs in: {RAW_DATA_DIR}\n")

    frames: dict[str, pd.DataFrame] = {}
    for name in ("agents", "categories", "comments", "tickets", "sla_breaches"):
        df = _load(name)
        if df is not None:
            frames[name] = df
            inspect_frame(name, df)

    if not frames:
        print("No CSVs found. Run download_dataset.py first.")
        return

    # Rough FK sanity checks between tickets and agents/categories/comments.
    if "tickets" in frames:
        tickets = frames["tickets"]
        ticket_id_col = _find_id_column(tickets, ["ticket_id", "id"])
        print(f"\n{'=' * 70}\nFOREIGN KEY CHECKS\n{'=' * 70}")
        if "comments" in frames and ticket_id_col:
            comments = frames["comments"]
            comment_fk_col = _find_id_column(comments, ["ticket_id", "incident_id"])
            if comment_fk_col:
                known_ids = set(tickets[ticket_id_col].astype(str))
                comment_ids = set(comments[comment_fk_col].astype(str))
                orphans = comment_ids - known_ids
                print(f"comments.{comment_fk_col} orphaned from tickets.{ticket_id_col}: {len(orphans)}")
        if "categories" in frames:
            cat_id_col = _find_id_column(frames["categories"], ["category_id", "id"])
            ticket_cat_col = next((c for c in tickets.columns if "categ" in c.lower()), None)
            if cat_id_col and ticket_cat_col:
                known_cats = set(frames["categories"][cat_id_col].astype(str))
                used_cats = set(tickets[ticket_cat_col].astype(str))
                orphans = used_cats - known_cats
                print(f"tickets.{ticket_cat_col} not found in categories.{cat_id_col}: {len(orphans)}")


if __name__ == "__main__":
    main()
