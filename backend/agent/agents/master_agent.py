from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import SystemMessage, HumanMessage

from agent.agents.base import BaseAgent
from agent.prompts.master import (
    MASTER_AGENT_SYSTEM_PROMPT,
    MASTER_TASK_DECOMPOSITION_PROMPT,
)
import structlog

logger = structlog.get_logger()


class MasterAgent(BaseAgent):
    """Master Agent: orchestrates the detection pipeline.

    Responsible for:
    - Task decomposition and planning
    - Coordinating crawler, detector, and reporter agents
    - Making strategic decisions about exploration vs testing
    - Aggregating results
    """

    def get_system_prompt(self) -> str:
        long_term_ctx = "No historical experience available."
        return MASTER_AGENT_SYSTEM_PROMPT.format(
            long_term_context=long_term_ctx,
            current_state="Initializing...",
        )

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute the master agent's decision loop."""
        target_url = input_data["target_url"]
        config = input_data.get("config", {})

        # Get long-term memory context
        from urllib.parse import urlparse
        domain = urlparse(target_url).netloc
        long_term_ctx = await self.long_term_memory.recall_for_context(domain)

        self.remember("task_start", f"Starting detection for {target_url}")

        return await self.decide_next_action(
            target_url=target_url,
            config=config,
            pages_discovered=input_data.get("pages_discovered", 0),
            pages_tested=input_data.get("pages_tested", 0),
            issues_found=input_data.get("issues_found", 0),
            pending_urls_count=input_data.get("pending_urls_count", 0),
            pending_test_urls_count=input_data.get("pending_test_urls_count", 0),
            max_pages=input_data.get("max_pages", 100),
        )

    async def decide_next_action(
        self,
        target_url: str,
        config: dict,
        pages_discovered: int,
        pages_tested: int,
        issues_found: int,
        pending_urls_count: int = 0,
        pending_test_urls_count: int = 0,
        max_pages: int = 100,
    ) -> dict[str, Any]:
        """Use LLM to decide the next action in the detection pipeline."""
        prompt = MASTER_TASK_DECOMPOSITION_PROMPT.format(
            target_url=target_url,
            config=json.dumps(config, ensure_ascii=False),
            pages_discovered=pages_discovered,
            pages_tested=pages_tested,
            issues_found=issues_found,
            pending_urls_count=pending_urls_count,
            pending_test_urls_count=pending_test_urls_count,
            max_pages=max_pages,
        )

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=prompt),
        ]

        response = await self.llm.ainvoke(messages)
        content = response.content

        # Parse JSON response
        try:
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            decision = json.loads(content.strip())
        except (json.JSONDecodeError, IndexError):
            logger.warning("master_parse_error", content=content[:200])
            decision = {
                "action": "EXPLORE" if pages_discovered == 0 else "TEST",
                "reasoning": "Failed to parse LLM response, using default action",
                "target_urls": [target_url],
                "priority": "medium",
            }

        self.remember("decision", json.dumps(decision, ensure_ascii=False))
        await self.notify("decision", decision)

        return decision
