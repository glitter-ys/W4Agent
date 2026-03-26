from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import SystemMessage, HumanMessage

from agent.agents.base import BaseAgent
from agent.prompts.reporter import (
    REPORTER_AGENT_SYSTEM_PROMPT,
    REPORTER_SUMMARY_PROMPT,
)
import structlog

logger = structlog.get_logger()


class ReporterAgent(BaseAgent):
    """Reporter Agent: generates accessibility detection reports.

    Responsible for:
    - Aggregating detection results
    - Generating compliance scores
    - Writing human-readable summaries and recommendations
    - Formatting reports for export
    """

    def get_system_prompt(self) -> str:
        return REPORTER_AGENT_SYSTEM_PROMPT

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Generate a report summary using LLM analysis."""
        total_pages = input_data.get("total_pages", 0)
        total_issues = input_data.get("total_issues", 0)
        critical_issues = input_data.get("critical_issues", 0)
        major_issues = input_data.get("major_issues", 0)
        minor_issues = input_data.get("minor_issues", 0)
        overall_score = input_data.get("overall_score", 0)
        issue_distribution = input_data.get("issue_distribution", {})

        prompt = REPORTER_SUMMARY_PROMPT.format(
            total_pages=total_pages,
            total_issues=total_issues,
            critical_issues=critical_issues,
            major_issues=major_issues,
            minor_issues=minor_issues,
            overall_score=overall_score,
            issue_distribution=json.dumps(issue_distribution, ensure_ascii=False),
        )

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=prompt),
        ]

        response = await self.llm.ainvoke(messages)
        content = response.content

        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content.strip())
        except (json.JSONDecodeError, IndexError):
            logger.warning("reporter_parse_error", content=content[:200])
            result = {
                "summary": f"检测了{total_pages}个页面，发现{total_issues}个无障碍问题，其中{critical_issues}个严重问题。",
                "recommendations": [
                    "优先修复严重级别的无障碍问题",
                    "为所有图片添加有意义的替代文本",
                    "确保页面可通过键盘完全操作",
                ],
            }

        self.remember("report_generated", json.dumps(result, ensure_ascii=False))
        return result
