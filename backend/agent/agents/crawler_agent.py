from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import SystemMessage, HumanMessage

from agent.agents.base import BaseAgent
from agent.prompts.crawler import (
    CRAWLER_AGENT_SYSTEM_PROMPT,
    CRAWLER_NEXT_ACTION_PROMPT,
)
import structlog

logger = structlog.get_logger()


class CrawlerAgent(BaseAgent):
    """Crawler Agent: intelligently explores web pages.

    Responsible for:
    - Deciding which pages to explore next
    - Identifying interactive elements on pages
    - Determining navigation strategies
    - Avoiding redundant page visits
    """

    def get_system_prompt(self) -> str:
        return CRAWLER_AGENT_SYSTEM_PROMPT.format(
            context=self.short_term_memory.get_context_summary(),
            current_url="",
            page_title="",
            a11y_tree_summary="",
        )

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Decide the next crawling action based on current page state."""
        current_url = input_data.get("current_url", "")
        page_title = input_data.get("page_title", "")
        interactive_elements = input_data.get("interactive_elements", [])
        explored_urls = input_data.get("explored_urls", [])
        pending_urls = input_data.get("pending_urls", [])
        a11y_tree_summary = input_data.get("a11y_tree_summary", "")

        system_prompt = CRAWLER_AGENT_SYSTEM_PROMPT.format(
            context=self.short_term_memory.get_context_summary(),
            current_url=current_url,
            page_title=page_title,
            a11y_tree_summary=a11y_tree_summary,
        )

        prompt = CRAWLER_NEXT_ACTION_PROMPT.format(
            interactive_elements=json.dumps(interactive_elements[:50], ensure_ascii=False),
            explored_urls=json.dumps(explored_urls[-20:], ensure_ascii=False),
            pending_urls=json.dumps(pending_urls[:20], ensure_ascii=False),
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt),
        ]

        response = await self.llm.ainvoke(messages)
        content = response.content

        # Parse JSON response
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            action = json.loads(content.strip())
        except (json.JSONDecodeError, IndexError):
            logger.warning("crawler_parse_error", content=content[:200])
            # Default: navigate to next pending URL
            next_url = pending_urls[0] if pending_urls else None
            action = {
                "action": "navigate" if next_url else "skip",
                "target": next_url,
                "reasoning": "Default action: navigate to next pending URL",
                "expected_outcome": "Load new page for exploration",
            }

        self.remember("crawl_action", json.dumps(action, ensure_ascii=False))
        return action
