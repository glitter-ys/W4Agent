from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dependencies import get_db
from app.core.security import get_current_user
from app.core.exceptions import NotFoundException
from app.models.report import Report
from app.schemas.report import ReportResponse, ReportExportRequest
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/task/{task_id}", response_model=ReportResponse)
async def get_report_by_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    result = await db.execute(select(Report).where(Report.task_id == task_id))
    report = result.scalar_one_or_none()
    if not report:
        raise NotFoundException("Report", str(task_id))
    return report


@router.post("/task/{task_id}/export")
async def export_report(
    task_id: UUID,
    payload: ReportExportRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Export report in specified format (html, pdf, json)."""
    result = await db.execute(select(Report).where(Report.task_id == task_id))
    report = result.scalar_one_or_none()
    if not report:
        raise NotFoundException("Report", str(task_id))

    file_path = await ReportService.export_report(report, payload.format)

    media_types = {
        "html": "text/html",
        "pdf": "application/pdf",
        "json": "application/json",
    }

    return FileResponse(
        path=file_path,
        media_type=media_types.get(payload.format, "application/octet-stream"),
        filename=f"report_{task_id}.{payload.format}",
    )
