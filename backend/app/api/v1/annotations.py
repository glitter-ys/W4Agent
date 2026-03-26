from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dependencies import get_db
from app.core.security import get_current_user
from app.core.exceptions import NotFoundException
from app.models.annotation import Annotation
from app.models.issue import Issue, IssueStatus
from app.schemas.annotation import AnnotationCreate, AnnotationResponse

router = APIRouter(prefix="/annotations", tags=["annotations"])


@router.post("/", response_model=AnnotationResponse, status_code=201)
async def create_annotation(
    payload: AnnotationCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    # Verify issue exists
    result = await db.execute(select(Issue).where(Issue.id == payload.issue_id))
    issue = result.scalar_one_or_none()
    if not issue:
        raise NotFoundException("Issue", str(payload.issue_id))

    annotation = Annotation(
        issue_id=payload.issue_id,
        user_id=user.get("sub", "unknown"),
        annotation_type=payload.annotation_type,
        content=payload.content,
        new_severity=payload.new_severity,
    )
    db.add(annotation)

    # Update issue status based on annotation type
    if payload.annotation_type.value == "confirm":
        issue.status = IssueStatus.CONFIRMED
    elif payload.annotation_type.value == "false_positive":
        issue.status = IssueStatus.FALSE_POSITIVE

    await db.commit()
    await db.refresh(annotation)
    return annotation


@router.get("/issue/{issue_id}", response_model=list[AnnotationResponse])
async def list_annotations_for_issue(
    issue_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(Annotation)
        .where(Annotation.issue_id == issue_id)
        .order_by(Annotation.created_at.desc())
    )
    return result.scalars().all()
