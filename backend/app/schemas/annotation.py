from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.annotation import AnnotationType


class AnnotationCreate(BaseModel):
    issue_id: UUID
    annotation_type: AnnotationType
    content: str | None = None
    new_severity: str | None = None


class AnnotationResponse(BaseModel):
    id: UUID
    issue_id: UUID
    user_id: str
    annotation_type: AnnotationType
    content: str | None
    new_severity: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
