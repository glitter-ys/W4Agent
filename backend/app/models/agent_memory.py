from __future__ import annotations

import enum

from sqlalchemy import String, Text, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class MemoryType(str, enum.Enum):
    EPISODIC = "episodic"      # Specific detection experiences
    SEMANTIC = "semantic"       # General knowledge about patterns
    PROCEDURAL = "procedural"  # How to handle specific page types


class AgentMemory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "agent_memories"

    memory_type: Mapped[MemoryType] = mapped_column(Enum(MemoryType), nullable=False)
    domain: Mapped[str] = mapped_column(String(512), nullable=False)
    key: Mapped[str] = mapped_column(String(512), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    relevance_score: Mapped[float | None] = mapped_column(nullable=True, default=1.0)
