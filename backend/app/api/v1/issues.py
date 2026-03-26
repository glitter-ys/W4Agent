from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.dependencies import get_db
from app.core.security import get_current_user
from app.core.exceptions import NotFoundException
from app.models.issue import Issue
from app.schemas.issue import IssueResponse, IssueUpdate, IssueListResponse

router = APIRouter(prefix="/issues", tags=["issues"])


@router.get("/", response_model=IssueListResponse)
async def list_issues(
    task_id: UUID | None = Query(None),
    page_id: UUID | None = Query(None),
    severity: str | None = Query(None),
    status: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    query = select(Issue)
    count_query = select(func.count(Issue.id))

    if task_id:
        query = query.where(Issue.task_id == task_id)
        count_query = count_query.where(Issue.task_id == task_id)
    if page_id:
        query = query.where(Issue.page_id == page_id)
        count_query = count_query.where(Issue.page_id == page_id)
    if severity:
        query = query.where(Issue.severity == severity)
        count_query = count_query.where(Issue.severity == severity)
    if status:
        query = query.where(Issue.status == status)
        count_query = count_query.where(Issue.status == status)

    total_q = await db.execute(count_query)
    total = total_q.scalar_one()

    result = await db.execute(
        query.order_by(Issue.created_at.desc()).offset(skip).limit(limit)
    )
    items = result.scalars().all()
    return IssueListResponse(items=items, total=total)


@router.get("/{issue_id}", response_model=IssueResponse)
async def get_issue(
    issue_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    result = await db.execute(select(Issue).where(Issue.id == issue_id))
    issue = result.scalar_one_or_none()
    if not issue:
        raise NotFoundException("Issue", str(issue_id))
    return issue


@router.patch("/{issue_id}", response_model=IssueResponse)
async def update_issue(
    issue_id: UUID,
    payload: IssueUpdate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    result = await db.execute(select(Issue).where(Issue.id == issue_id))
    issue = result.scalar_one_or_none()
    if not issue:
        raise NotFoundException("Issue", str(issue_id))

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(issue, field, value)

    await db.commit()
    await db.refresh(issue)
    return issue
