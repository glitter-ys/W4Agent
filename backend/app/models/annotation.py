from __future__ import annotations

import enum

from sqlalchemy import String, Text, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class AnnotationType(str, enum.Enum):
    CONFIRM = "confirm"
    FALSE_POSITIVE = "false_positive"
    RECLASSIFY = "reclassify"
    COMMENT = "comment"


class Annotation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "annotations"

    issue_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("issues.id"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    annotation_type: Mapped[AnnotationType] = mapped_column(Enum(AnnotationType), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_severity: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Relationships
    issue = relationship("Issue", back_populates="annotations")
