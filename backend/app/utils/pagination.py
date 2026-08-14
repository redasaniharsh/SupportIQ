"""Pagination helpers shared by all list endpoints.

Default page=1 / page_size=20, max page_size=100. Response envelope:
    {"items": [...], "page": 1, "page_size": 20, "total": 123, "total_pages": 7}
"""
from __future__ import annotations

import math
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

T = TypeVar("T")


def clamp_pagination(page: int | None, page_size: int | None) -> tuple[int, int]:
    page = page or DEFAULT_PAGE
    page_size = page_size or DEFAULT_PAGE_SIZE
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = DEFAULT_PAGE_SIZE
    if page_size > MAX_PAGE_SIZE:
        page_size = MAX_PAGE_SIZE
    return page, page_size


def compute_total_pages(total: int, page_size: int) -> int:
    if page_size <= 0:
        return 0
    return max(1, math.ceil(total / page_size)) if total > 0 else 0


def compute_skip(page: int, page_size: int) -> int:
    return (page - 1) * page_size


def build_page_envelope(items: list[Any], *, page: int, page_size: int, total: int) -> dict:
    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": compute_total_pages(total, page_size),
    }
