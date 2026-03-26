from __future__ import annotations

import enum

from sqlalchemy import String, Text, Enum, ForeignKey, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class IssueSeverity(str, enum.Enum):
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    INFO = "info"


class IssueStatus(str, enum.Enum):
    OPEN = "open"
    CONFIRMED = "confirmed"
    FALSE_POSITIVE = "false_positive"
    FIXED = "fixed"
    WONT_FIX = "wont_fix"


class WCAGLevel(str, enum.Enum):
    A = "A"
    AA = "AA"
    AAA = "AAA"


class Issue(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "issues"

    task_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False
    )
    page_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pages.id"), nullable=False
    )

    # WCAG classification
    wcag_criterion: Mapped[str] = mapped_column(String(20), nullable=False)
    wcag_level: Mapped[WCAGLevel] = mapped_column(Enum(WCAGLevel), nullable=False)
    rule_id: Mapped[str] = mapped_column(String(100), nullable=False)

    # Issue details
    severity: Mapped[IssueSeverity] = mapped_column(Enum(IssueSeverity), nullable=False)
    status: Mapped[IssueStatus] = mapped_column(
        Enum(IssueStatus), default=IssueStatus.OPEN, nullable=False
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Element location
    element_selector: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    element_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    screenshot_path: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Detection source
    detected_by: Mapped[str] = mapped_column(String(50), nullable=False)  # "rule" or "ai"
    confidence: Mapped[float | None] = mapped_column(nullable=True)

    # Context data
    context: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Jira integration
    jira_issue_key: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationships
    task = relationship("Task", back_populates="issues")
    page = relationship("Page", back_populates="issues")
    annotations = relationship("Annotation", back_populates="issue", cascade="all, delete-orphan")
