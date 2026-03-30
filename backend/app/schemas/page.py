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
    content_hash: str | None = None
    screenshot_path: str | None
    annotated_screenshot_path: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PageListResponse(BaseModel):
    items: list[PageResponse]
    total: int
