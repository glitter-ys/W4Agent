from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.dependencies import get_db
from app.core.security import get_current_user
from app.core.exceptions import NotFoundException, TaskAlreadyRunningException
from app.models.task import Task, TaskStatus
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse,
)
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(
    payload: TaskCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Create a detection task and optionally start it in the background."""
    task = Task(
        project_id=payload.project_id,
        name=payload.name,
        target_url=payload.target_url,
        config=payload.config.model_dump(),
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.get("/", response_model=TaskListResponse)
async def list_tasks(
    project_id: UUID | None = Query(None),
    status: TaskStatus | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    query = select(Task)
    count_query = select(func.count(Task.id))

    if project_id:
        query = query.where(Task.project_id == project_id)
        count_query = count_query.where(Task.project_id == project_id)
    if status:
        query = query.where(Task.status == status)
        count_query = count_query.where(Task.status == status)

    total_q = await db.execute(count_query)
    total = total_q.scalar_one()

    result = await db.execute(
        query.order_by(Task.created_at.desc()).offset(skip).limit(limit)
    )
    items = result.scalars().all()
    return TaskListResponse(items=items, total=total)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise NotFoundException("Task", str(task_id))
    return task


@router.post("/{task_id}/start", response_model=TaskResponse)
async def start_task(
    task_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Start a pending task. Launches the agent engine in the background."""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise NotFoundException("Task", str(task_id))
    if task.status == TaskStatus.RUNNING:
        raise TaskAlreadyRunningException(str(task_id))

    task.status = TaskStatus.RUNNING
    await db.commit()
    await db.refresh(task)

    # Launch agent engine in background
    background_tasks.add_task(TaskService.run_detection, str(task_id))

    return task


@router.post("/{task_id}/stop", response_model=TaskResponse)
async def stop_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Stop a running task."""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise NotFoundException("Task", str(task_id))

    task.status = TaskStatus.CANCELLED
    await db.commit()
    await db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise NotFoundException("Task", str(task_id))

    await db.delete(task)
    await db.commit()
