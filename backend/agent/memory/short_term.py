from __future__ import annotations

from dataclasses import dataclass, field
from collections import deque


@dataclass
class ShortTermMemory:
    """In-session working memory for an agent.

    Stores recent observations, actions, and reasoning within a single
    detection task. Uses a bounded deque to prevent unbounded growth.
    """

    max_entries: int = 100
    _entries: deque = field(default_factory=lambda: deque(maxlen=100))

    def __post_init__(self):
        self._entries = deque(maxlen=self.max_entries)

    def add(self, entry_type: str, content: str, metadata: dict | None = None):
        self._entries.append({
            "type": entry_type,
            "content": content,
            "metadata": metadata or {},
        })

    def get_recent(self, n: int = 10, entry_type: str | None = None) -> list[dict]:
        entries = list(self._entries)
        if entry_type:
            entries = [e for e in entries if e["type"] == entry_type]
        return entries[-n:]

    def get_context_summary(self) -> str:
        """Return a concise summary of recent memory for LLM context."""
        recent = self.get_recent(20)
        if not recent:
            return "No prior observations."

        lines = []
        for entry in recent:
            lines.append(f"[{entry['type']}] {entry['content']}")
        return "\n".join(lines)

    def clear(self):
        self._entries.clear()

    @property
    def size(self) -> int:
        return len(self._entries)
