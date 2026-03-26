from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from langchain_core.language_models import BaseChatModel

from agent.memory.short_term import ShortTermMemory
from agent.memory.long_term import LongTermMemory


class BaseAgent(ABC):
    """Abstract base class for all agents in the system.

    Each agent has:
    - An LLM for reasoning
    - Short-term memory (within a task)
    - Access to long-term memory (across tasks)
    - A set of tools it can use
    """

    def __init__(
        self,
        name: str,
        llm: BaseChatModel,
        task_id: str,
        short_term_memory: ShortTermMemory | None = None,
        long_term_memory: LongTermMemory | None = None,
    ):
        self.name = name
        self.llm = llm
        self.task_id = task_id
        self.short_term_memory = short_term_memory or ShortTermMemory()
        self.long_term_memory = long_term_memory or LongTermMemory()

    @abstractmethod
    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute the agent's main logic."""
        ...

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the agent's system prompt."""
        ...

    async def notify(self, message_type: str, data: dict):
        """Send real-time notification via WebSocket."""
        from app.services.notification_service import NotificationService
        await NotificationService.notify_agent_reasoning(
            task_id=self.task_id,
            agent_name=self.name,
            reasoning=str(data),
        )

    def remember(self, entry_type: str, content: str, metadata: dict | None = None):
        """Add an entry to short-term memory."""
        self.short_term_memory.add(entry_type, content, metadata)
