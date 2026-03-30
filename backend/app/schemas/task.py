from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.task import TaskStatus


class TaskConfig(BaseModel):
    max_depth: int = 5
    max_pages: int = 100
    wcag_level: str = "AA"
    include_patterns: list[str] = []
    exclude_patterns: list[str] = []
    viewport_width: int = 1280
    viewport_height: int = 720
    enable_ai_detection: bool = True
    enable_screenshots: bool = True
    enable_vision_detection: bool = False


class TaskCreate(BaseModel):
    project_id: UUID
    name: str
    target_url: str
    config: TaskConfig = TaskConfig()


class TaskUpdate(BaseModel):
    name: str | None = None
    status: TaskStatus | None = None
    config: TaskConfig | None = None


class TaskResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    target_url: str
    status: TaskStatus
    config: dict | None
    pages_discovered: int
    pages_tested: int
    issues_found: int
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    items: list[TaskResponse]
    total: int


class TaskProgress(BaseModel):
    """Real-time task progress data sent via WebSocket."""
    task_id: str
    status: TaskStatus
    pages_discovered: int
    pages_tested: int
    issues_found: int
    current_url: str | None = None
    current_action: str | None = None
    agent_reasoning: str | None = None
