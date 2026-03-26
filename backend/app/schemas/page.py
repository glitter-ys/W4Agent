from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.page import PageStatus


class PageResponse(BaseModel):
    id: UUID
    task_id: UUID
    url: str
    title: str | None
    status: PageStatus
    depth: int
    screenshot_path: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PageListResponse(BaseModel):
    items: list[PageResponse]
    total: int
