from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import SystemMessage, HumanMessage

from agent.agents.base import BaseAgent
from agent.prompts.detector import (
    DETECTOR_AGENT_SYSTEM_PROMPT,
    DETECTOR_PAGE_ANALYSIS_PROMPT,
)
import structlog

logger = structlog.get_logger()


class DetectorAgent(BaseAgent):
    """Detector Agent: performs accessibility testing on pages.

    Combines rule-based checking with AI-powered analysis to find
    accessibility issues that pure rule engines miss.
    """

    def get_system_prompt(self) -> str:
        return DETECTOR_AGENT_SYSTEM_PROMPT

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Analyze a page for accessibility issues using AI."""
        url = input_data.get("url", "")
        title = input_data.get("title", "")
        a11y_tree = input_data.get("a11y_tree", "")
        html_snippet = input_data.get("html_snippet", "")
        rule_issues = input_data.get("rule_issues", [])

        prompt = DETECTOR_PAGE_ANALYSIS_PROMPT.format(
            url=url,
            title=title,
            a11y_tree=json.dumps(a11y_tree, ensure_ascii=False) if isinstance(a11y_tree, dict) else str(a11y_tree),
            html_snippet=html_snippet[:5000],  # Limit HTML size
            rule_issues=json.dumps(rule_issues, ensure_ascii=False),
        )

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=prompt),
        ]

        response = await self.llm.ainvoke(messages)
        content = response.content

        # Parse JSON array response
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            ai_issues = json.loads(content.strip())
            if not isinstance(ai_issues, list):
                ai_issues = [ai_issues]
        except (json.JSONDecodeError, IndexError):
            logger.warning("detector_parse_error", content=content[:200])
            ai_issues = []

        # Merge with rule-based issues
        all_issues = rule_issues + [
            {**issue, "detected_by": "ai"} for issue in ai_issues
        ]

        self.remember(
            "detection_result",
            f"Found {len(ai_issues)} AI issues + {len(rule_issues)} rule issues for {url}",
        )

        return {
            "url": url,
            "rule_issues": rule_issues,
            "ai_issues": ai_issues,
            "all_issues": all_issues,
            "total_count": len(all_issues),
        }

    async def analyze_screenshot(self, screenshot_path: str, page_url: str) -> list[dict]:
        """Use vision LLM to analyze a page screenshot for visual accessibility issues."""
        from agent.llm.provider import get_vision_llm
        import base64

        try:
            with open(screenshot_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode()
        except FileNotFoundError:
            logger.warning("screenshot_not_found", path=screenshot_path)
            return []

        vision_llm = get_vision_llm()

        messages = [
            SystemMessage(content="你是一名Web无障碍专家。请分析这个网页截图，找出视觉层面的无障碍问题。"),
            HumanMessage(content=[
                {"type": "text", "text": f"请分析这个网页截图（{page_url}）的视觉无障碍问题，包括：\n1. 文字颜色对比度是否足够\n2. 按钮和链接是否容易辨识\n3. 布局是否适合屏幕阅读器\n4. 是否有闪烁或动画问题\n\n请以JSON数组格式返回发现的问题。"},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}},
            ]),
        ]

        response = await vision_llm.ainvoke(messages)
        content = response.content

        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            issues = json.loads(content.strip())
            if not isinstance(issues, list):
                issues = [issues]
            return issues
        except (json.JSONDecodeError, IndexError):
            return []
