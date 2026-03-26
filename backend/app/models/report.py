from __future__ import annotations

from sqlalchemy import String, Text, Float, Integer, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class Report(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "reports"

    task_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id"), unique=True, nullable=False
    )

    # Compliance scores
    overall_score: Mapped[float] = mapped_column(Float, default=0.0)
    level_a_score: Mapped[float] = mapped_column(Float, default=0.0)
    level_aa_score: Mapped[float] = mapped_column(Float, default=0.0)
    level_aaa_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Statistics
    total_pages: Mapped[int] = mapped_column(Integer, default=0)
    total_issues: Mapped[int] = mapped_column(Integer, default=0)
    critical_issues: Mapped[int] = mapped_column(Integer, default=0)
    major_issues: Mapped[int] = mapped_column(Integer, default=0)
    minor_issues: Mapped[int] = mapped_column(Integer, default=0)

    # Summary content
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendations: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Report file paths
    html_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    pdf_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    json_path: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Detailed breakdown (JSON)
    issue_breakdown: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    page_results: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships
    task = relationship("Task", back_populates="report")
