from __future__ import annotations

import enum

from sqlalchemy import String, Text, Integer, Float, Enum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class PageStatus(str, enum.Enum):
    DISCOVERED = "discovered"
    CRAWLING = "crawling"
    TESTING = "testing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Page(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "pages"

    task_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False
    )
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[PageStatus] = mapped_column(
        Enum(PageStatus), default=PageStatus.DISCOVERED, nullable=False
    )
    depth: Mapped[int] = mapped_column(Integer, default=0)

    # Page fingerprint for deduplication
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    semantic_similarity: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Screenshot path
    screenshot_path: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Annotated screenshot path (with visual issue markers)
    annotated_screenshot_path: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # A11y tree snapshot (JSON)
    a11y_tree: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Page metadata
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships
    task = relationship("Task", back_populates="pages")
    issues = relationship("Issue", back_populates="page", cascade="all, delete-orphan")
