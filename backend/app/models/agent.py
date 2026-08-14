"""Agent model — support staff who can be assigned to incidents."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class Agent(BaseModel):
    agent_id: str
    name: str
    email: Optional[str] = None
    team: Optional[str] = None
    role: Optional[str] = None
    source_data: dict = Field(default_factory=dict)
