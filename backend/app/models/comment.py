"""Comment model — stored as separate documents, not embedded in incidents."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.utils.dates import utcnow


class Comment(BaseModel):
    comment_id: str
    incident_id: str
    author: Optional[str] = None
    author_id: Optional[str] = None
    body: str
    is_internal: bool = False
    source_data: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)
