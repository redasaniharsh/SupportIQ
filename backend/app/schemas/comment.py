"""Comment request/response schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CommentCreateRequest(BaseModel):
    body: str = Field(..., min_length=1)
    author: Optional[str] = None
    author_id: Optional[str] = None
    is_internal: bool = False


class CommentResponse(BaseModel):
    comment_id: str
    incident_id: str
    author: Optional[str] = None
    author_id: Optional[str] = None
    body: str
    is_internal: bool
    created_at: datetime

    model_config = {"from_attributes": True}
