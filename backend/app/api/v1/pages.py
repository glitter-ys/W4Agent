from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.page import Page
from app.schemas.page import PageResponse, PageListResponse

router = APIRouter(prefix="/pages", tags=["pages"])


@router.get("/", response_model=PageListResponse)
async def list_pages(
    task_id: str = Query(..., description="Task ID to filter pages"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """List all pages for a given task."""
    base_query = select(Page).where(Page.task_id == task_id)

    # Count total
    count_query = select(func.count()).select_from(base_query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Fetch items
    items_query = base_query.order_by(Page.created_at).offset(skip).limit(limit)
    result = await db.execute(items_query)
    pages = result.scalars().all()

    return PageListResponse(items=pages, total=total)


@router.get("/{page_id}", response_model=PageResponse)
async def get_page(
    page_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a single page by ID."""
    result = await db.execute(select(Page).where(Page.id == page_id))
    page = result.scalar_one_or_none()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return page
