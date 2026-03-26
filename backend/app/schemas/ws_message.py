from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class WSMessageType(str, Enum):
    TASK_PROGRESS = "task_progress"
    PAGE_DISCOVERED = "page_discovered"
    PAGE_TESTED = "page_tested"
    ISSUE_FOUND = "issue_found"
    AGENT_REASONING = "agent_reasoning"
    EVENT_DETECTED = "event_detected"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    ERROR = "error"


class WSMessage(BaseModel):
    type: WSMessageType
    task_id: str
    data: dict
    timestamp: str | None = None
