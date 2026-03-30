from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.issue import IssueSeverity, IssueStatus, WCAGLevel


class IssueResponse(BaseModel):
    id: UUID
    task_id: UUID
    page_id: UUID
    wcag_criterion: str
    wcag_level: WCAGLevel
    rule_id: str
    severity: IssueSeverity
    status: IssueStatus
    title: str
    description: str
    recommendation: str | None
    element_selector: str | None
    element_html: str | None
    screenshot_path: str | None
    detected_by: str
    confidence: float | None
    context: dict | None = None
    jira_issue_key: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class IssueUpdate(BaseModel):
    status: IssueStatus | None = None
    severity: IssueSeverity | None = None


class IssueListResponse(BaseModel):
    items: list[IssueResponse]
    total: int
