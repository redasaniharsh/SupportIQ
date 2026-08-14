"""Category model — mirrors DESIGN.md incident.category shape plus a
standalone `categories` collection document."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class CategoryRef(BaseModel):
    """Embedded category reference used inside an incident document."""

    id: Optional[int] = None
    name: str
    service: Optional[str] = None


class Category(BaseModel):
    """Standalone document in the `categories` collection."""

    category_id: int
    name: str
    service: Optional[str] = None
    description: Optional[str] = None
    source_data: dict = Field(default_factory=dict)
