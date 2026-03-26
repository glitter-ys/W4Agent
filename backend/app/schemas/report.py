from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ReportResponse(BaseModel):
    id: UUID
    task_id: UUID
    overall_score: float
    level_a_score: float
    level_aa_score: float
    level_aaa_score: float
    total_pages: int
    total_issues: int
    critical_issues: int
    major_issues: int
    minor_issues: int
    summary: str | None
    recommendations: str | None
    issue_breakdown: dict | None
    page_results: dict | None
    html_path: str | None
    pdf_path: str | None
    json_path: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportExportRequest(BaseModel):
    format: str = "html"  # html, pdf, json
