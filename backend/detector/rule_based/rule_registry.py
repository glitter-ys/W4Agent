from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class A11yRule(ABC):
    """Abstract base class for accessibility check rules."""

    @property
    @abstractmethod
    def rule_id(self) -> str:
        """Unique identifier for this rule."""
        ...

    @property
    @abstractmethod
    def wcag_criterion(self) -> str:
        """WCAG success criterion this rule checks (e.g., '1.1.1')."""
        ...

    @property
    @abstractmethod
    def wcag_level(self) -> str:
        """WCAG conformance level (A, AA, AAA)."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what this rule checks."""
        ...

    @abstractmethod
    def check(self, page_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Run this rule against page data and return any issues found.

        Returns a list of issue dictionaries with keys:
        - rule_id, wcag_criterion, wcag_level
        - severity, title, description, recommendation
        - element_selector, element_html
        - detected_by: "rule"
        """
        ...


class RuleRegistry:
    """Registry of all accessibility check rules."""

    def __init__(self):
        self._rules: list[A11yRule] = []

    def register(self, rule: A11yRule):
        self._rules.append(rule)

    def get_rules(
        self,
        wcag_level: str = "AA",
    ) -> list[A11yRule]:
        """Get all rules up to the specified WCAG level."""
        level_order = {"A": 0, "AA": 1, "AAA": 2}
        max_level = level_order.get(wcag_level, 1)

        return [
            r for r in self._rules
            if level_order.get(r.wcag_level, 0) <= max_level
        ]

    def run_all(self, page_data: dict, wcag_level: str = "AA") -> list[dict]:
        """Run all applicable rules and collect issues."""
        issues = []
        for rule in self.get_rules(wcag_level):
            try:
                rule_issues = rule.check(page_data)
                issues.extend(rule_issues)
            except Exception as e:
                issues.append({
                    "rule_id": rule.rule_id,
                    "severity": "info",
                    "title": f"Rule {rule.rule_id} execution error",
                    "description": str(e),
                    "detected_by": "rule",
                })
        return issues


# Global registry instance
registry = RuleRegistry()
