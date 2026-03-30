from __future__ import annotations

import base64
import json
from typing import Any

from langchain_core.messages import SystemMessage, HumanMessage

from agent.agents.base import BaseAgent
from agent.prompts.detector import (
    DETECTOR_AGENT_SYSTEM_PROMPT,
    DETECTOR_PAGE_ANALYSIS_PROMPT,
    DETECTOR_VISION_ANALYSIS_PROMPT,
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
        screenshot_path = input_data.get("screenshot_path")
        bounding_boxes = input_data.get("bounding_boxes", [])

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

        # Run multimodal vision analysis if screenshot is available
        vision_issues = []
        if screenshot_path and bounding_boxes:
            vision_issues = await self.analyze_multimodal(
                screenshot_path=screenshot_path,
                url=url,
                title=title,
                bounding_boxes=bounding_boxes,
                a11y_tree=a11y_tree,
                rule_issues=rule_issues,
            )

            # Deduplicate: skip vision issues whose element_selector already exists
            existing_selectors = set()
            for issue in rule_issues + ai_issues:
                sel = issue.get("element_selector")
                if sel:
                    existing_selectors.add(sel)

            vision_issues = [
                issue for issue in vision_issues
                if issue.get("element_selector") not in existing_selectors
            ]

        # Merge with rule-based issues
        all_issues = rule_issues + [
            {**issue, "detected_by": "ai"} for issue in ai_issues
        ] + [
            {**issue, "detected_by": "vision_ai"} for issue in vision_issues
        ]

        self.remember(
            "detection_result",
            f"Found {len(ai_issues)} AI issues + {len(vision_issues)} vision issues + {len(rule_issues)} rule issues for {url}",
        )

        return {
            "url": url,
            "rule_issues": rule_issues,
            "ai_issues": ai_issues,
            "vision_issues": vision_issues,
            "all_issues": all_issues,
            "total_count": len(all_issues),
        }

    async def analyze_multimodal(
        self,
        screenshot_path: str,
        url: str,
        title: str,
        bounding_boxes: list[dict],
        a11y_tree: Any = None,
        rule_issues: list[dict] | None = None,
    ) -> list[dict]:
        """Use vision LLM to analyze screenshot with element context for visual a11y issues."""
        from agent.llm.provider import get_vision_llm

        try:
            with open(screenshot_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode()
        except FileNotFoundError:
            logger.warning("screenshot_not_found", path=screenshot_path)
            return []

        # Prepare element info for the prompt (limit to keep token count manageable)
        elements_summary = []
        for bbox_info in bounding_boxes[:80]:
            elements_summary.append({
                "selector": bbox_info.get("selector", ""),
                "tag": bbox_info.get("tag", ""),
                "text": bbox_info.get("text", "")[:60],
                "alt": bbox_info.get("alt"),
                "aria_label": bbox_info.get("aria_label"),
                "role": bbox_info.get("role"),
                "bbox": bbox_info.get("bbox", {}),
            })

        prompt_text = DETECTOR_VISION_ANALYSIS_PROMPT.format(
            url=url,
            title=title,
            elements_json=json.dumps(elements_summary, ensure_ascii=False, indent=2),
            rule_issues=json.dumps(rule_issues or [], ensure_ascii=False),
        )

        vision_llm = get_vision_llm()

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=[
                {"type": "text", "text": prompt_text},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}},
            ]),
        ]

        try:
            response = await vision_llm.ainvoke(messages)
            content = response.content

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            issues = json.loads(content.strip())
            if not isinstance(issues, list):
                issues = [issues]

            logger.info("vision_analysis_complete", url=url, issues_found=len(issues))
            return issues
        except Exception as e:
            logger.warning("vision_analysis_error", url=url, error=str(e))
            return []

    async def analyze_screenshot(self, screenshot_path: str, page_url: str) -> list[dict]:
        """Use vision LLM to analyze a page screenshot for visual accessibility issues."""
        from agent.llm.provider import get_vision_llm

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
