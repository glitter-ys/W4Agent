from __future__ import annotations

import io
import zipfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
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


# NOTE: This route must be defined BEFORE /{page_id} to avoid path conflict.
@router.get("/task/{task_id}/screenshots/download")
async def download_task_screenshots(
    task_id: str,
    annotated: bool = Query(True, description="Include annotated screenshots"),
    db: AsyncSession = Depends(get_db),
):
    """Download all screenshots for a task as a ZIP archive."""
    result = await db.execute(
        select(Page).where(Page.task_id == task_id).order_by(Page.created_at)
    )
    pages = result.scalars().all()

    if not pages:
        raise HTTPException(status_code=404, detail="No pages found for this task")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for idx, page in enumerate(pages, 1):
            # Sanitize page title for use as filename
            title = (page.title or page.url or f"page_{idx}").replace("/", "_").replace("\\", "_")
            title = title[:80]  # Limit length

            # Original screenshot
            if page.screenshot_path:
                orig_path = Path(page.screenshot_path)
                if orig_path.exists():
                    zf.write(orig_path, f"{idx:02d}_{title}.png")

            # Annotated screenshot
            if annotated and page.annotated_screenshot_path:
                ann_path = Path(page.annotated_screenshot_path)
                if ann_path.exists():
                    zf.write(ann_path, f"{idx:02d}_{title}_annotated.png")

    buf.seek(0)

    if buf.getbuffer().nbytes <= 22:  # Empty ZIP is ~22 bytes
        raise HTTPException(status_code=404, detail="No screenshot files found")

    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="screenshots_{task_id}.zip"',
        },
    )


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


@router.get("/{page_id}/screenshot")
async def download_page_screenshot(
    page_id: str,
    annotated: bool = Query(False, description="Download annotated version"),
    db: AsyncSession = Depends(get_db),
):
    """Download a single page screenshot."""
    result = await db.execute(select(Page).where(Page.id == page_id))
    page = result.scalar_one_or_none()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    path_str = page.annotated_screenshot_path if annotated else page.screenshot_path
    if not path_str:
        raise HTTPException(status_code=404, detail="Screenshot not found")

    file_path = Path(path_str)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Screenshot file not found")

    filename = file_path.name
    return FileResponse(
        path=str(file_path),
        media_type="image/png",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
