from __future__ import annotations

import json

import structlog

from app.db.session import async_session_factory
from app.models.agent_memory import AgentMemory, MemoryType
from sqlalchemy import select, text

logger = structlog.get_logger()


class LongTermMemory:
    """Cross-task persistent memory stored in PostgreSQL.

    Stores detection experiences, patterns, and procedural knowledge
    that can be retrieved for future tasks.
    """

    async def store(
        self,
        memory_type: MemoryType,
        domain: str,
        key: str,
        content: str,
        metadata: dict | None = None,
    ):
        """Store a memory entry."""
        async with async_session_factory() as db:
            memory = AgentMemory(
                memory_type=memory_type,
                domain=domain,
                key=key,
                content=content,
                metadata_json=metadata,
            )
            db.add(memory)
            await db.commit()
            logger.info("memory_stored", type=memory_type.value, domain=domain, key=key)

    async def recall(
        self,
        domain: str | None = None,
        memory_type: MemoryType | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """Retrieve memories matching criteria."""
        async with async_session_factory() as db:
            query = select(AgentMemory).order_by(AgentMemory.relevance_score.desc())

            if domain:
                query = query.where(AgentMemory.domain == domain)
            if memory_type:
                query = query.where(AgentMemory.memory_type == memory_type)

            query = query.limit(limit)
            result = await db.execute(query)
            memories = result.scalars().all()

            return [
                {
                    "type": m.memory_type.value,
                    "domain": m.domain,
                    "key": m.key,
                    "content": m.content,
                    "metadata": m.metadata_json,
                }
                for m in memories
            ]

    async def recall_for_context(self, domain: str, limit: int = 5) -> str:
        """Get formatted memory context for LLM prompts."""
        memories = await self.recall(domain=domain, limit=limit)
        if not memories:
            return "No historical experience for this domain."

        lines = ["Historical experience for this domain:"]
        for m in memories:
            lines.append(f"- [{m['type']}] {m['key']}: {m['content']}")
        return "\n".join(lines)

    async def store_detection_experience(
        self,
        domain: str,
        page_type: str,
        issues_found: list[str],
        strategies_used: list[str],
    ):
        """Store a detection experience for future reference."""
        content = json.dumps({
            "page_type": page_type,
            "issues_found": issues_found,
            "strategies_used": strategies_used,
        }, ensure_ascii=False)

        await self.store(
            memory_type=MemoryType.EPISODIC,
            domain=domain,
            key=f"detection_{page_type}",
            content=content,
            metadata={"issue_count": len(issues_found)},
        )
