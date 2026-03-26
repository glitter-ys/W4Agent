from __future__ import annotations

from typing import Any

import structlog

from detector.rule_based.rule_registry import registry

logger = structlog.get_logger()


class DetectionEngine:
    """Main detection engine that coordinates rule-based and AI-based checks.

    The rule-based engine runs first to catch clear violations.
    The AI-based engine then analyzes what rules might miss (semantic quality,
    visual issues, interaction patterns).
    """

    def __init__(self, wcag_level: str = "AA"):
        self.wcag_level = wcag_level

    async def detect(self, page_data: dict[str, Any]) -> list[dict]:
        """Run all rule-based detections on a page.

        Args:
            page_data: Page analysis data from PageAnalyzer

        Returns:
            List of detected issues
        """
        # Import rules to trigger registration
        import detector.rule_based.wcag_rules  # noqa: F401

        issues = registry.run_all(page_data, wcag_level=self.wcag_level)

        logger.info(
            "rule_detection_complete",
            url=page_data.get("url", "unknown"),
            issues_count=len(issues),
        )

        return issues

    async def detect_full(self, page_data: dict[str, Any], task_id: str) -> list[dict]:
        """Run both rule-based and AI-based detection.

        Args:
            page_data: Page analysis data from PageAnalyzer
            task_id: Current task ID for agent context

        Returns:
            Combined list of all detected issues
        """
        # Rule-based detection
        rule_issues = await self.detect(page_data)

        # AI-based detection
        from agent.agents.detector_agent import DetectorAgent
        from agent.llm.provider import get_llm
        from agent.memory.short_term import ShortTermMemory

        detector = DetectorAgent(
            name="Detector",
            llm=get_llm(),
            task_id=task_id,
            short_term_memory=ShortTermMemory(),
        )

        ai_result = await detector.run({
            "url": page_data.get("url", ""),
            "title": page_data.get("title", ""),
            "a11y_tree": page_data.get("a11y_tree", {}),
            "html_snippet": page_data.get("html", "")[:5000],
            "rule_issues": rule_issues,
        })

        all_issues = ai_result.get("all_issues", rule_issues)

        logger.info(
            "full_detection_complete",
            url=page_data.get("url", "unknown"),
            rule_issues=len(rule_issues),
            ai_issues=len(ai_result.get("ai_issues", [])),
            total_issues=len(all_issues),
        )

        return all_issues
