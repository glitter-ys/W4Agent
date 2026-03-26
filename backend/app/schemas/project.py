from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, HttpUrl


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    base_url: str


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    base_url: str | None = None


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    base_url: str
    owner: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]
    total: int
