from __future__ import annotations

import re
from typing import Any

from detector.rule_based.rule_registry import A11yRule, registry


class ImageAltTextRule(A11yRule):
    """WCAG 1.1.1 - Non-text Content: Images must have alt attributes."""

    rule_id = "img-alt"
    wcag_criterion = "1.1.1"
    wcag_level = "A"
    description = "All images must have alternative text"

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        for img in page_data.get("images", []):
            if not img.get("has_alt"):
                issues.append({
                    "rule_id": self.rule_id,
                    "wcag_criterion": self.wcag_criterion,
                    "wcag_level": self.wcag_level,
                    "severity": "critical",
                    "title": "Image missing alt attribute",
                    "description": f"Image element is missing the alt attribute. Source: {img.get('src', 'unknown')[:100]}",
                    "recommendation": "Add a descriptive alt attribute to the image. Use alt=\"\" for decorative images.",
                    "element_selector": f"img[src*='{img.get('src', '')[:50]}']",
                    "detected_by": "rule",
                })
            elif img.get("alt", "").strip() == "" and img.get("role") != "presentation":
                # Empty alt without presentation role — might be intentional for decorative
                pass  # Not flagging empty alt, as it may be decorative
        return issues


class EmptyAltTextRule(A11yRule):
    """Check for images with meaningless alt text (e.g., 'image', 'photo')."""

    rule_id = "img-alt-quality"
    wcag_criterion = "1.1.1"
    wcag_level = "A"
    description = "Image alt text should be meaningful"

    MEANINGLESS_ALT = {"image", "photo", "picture", "img", "图片", "图", "照片", "banner", "icon"}

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        for img in page_data.get("images", []):
            alt = (img.get("alt") or "").strip().lower()
            if alt in self.MEANINGLESS_ALT:
                issues.append({
                    "rule_id": self.rule_id,
                    "wcag_criterion": self.wcag_criterion,
                    "wcag_level": self.wcag_level,
                    "severity": "major",
                    "title": "Image has meaningless alt text",
                    "description": f"Image alt text '{alt}' is not descriptive. It should describe the image content.",
                    "recommendation": "Replace with a descriptive alternative text that conveys the image's purpose.",
                    "detected_by": "rule",
                })
        return issues


class FormLabelRule(A11yRule):
    """WCAG 1.3.1 / 4.1.2 - Form controls must have labels."""

    rule_id = "form-label"
    wcag_criterion = "1.3.1"
    wcag_level = "A"
    description = "Form controls must have associated labels"

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        for form in page_data.get("forms", []):
            for input_el in form.get("inputs", []):
                input_type = input_el.get("type", "")
                if input_type in ("hidden", "submit", "button", "reset", "image"):
                    continue

                has_label = input_el.get("has_label", False)
                has_aria = bool(input_el.get("aria_label"))
                has_placeholder = bool(input_el.get("placeholder"))

                if not has_label and not has_aria:
                    severity = "critical" if not has_placeholder else "major"
                    issues.append({
                        "rule_id": self.rule_id,
                        "wcag_criterion": self.wcag_criterion,
                        "wcag_level": self.wcag_level,
                        "severity": severity,
                        "title": "Form control missing label",
                        "description": f"Form input '{input_el.get('name', 'unnamed')}' (type: {input_type}) has no associated label or aria-label.",
                        "recommendation": "Add a <label> element with a 'for' attribute matching the input's id, or add aria-label.",
                        "element_selector": f"input[name='{input_el.get('name', '')}']",
                        "detected_by": "rule",
                    })
        return issues


class HeadingHierarchyRule(A11yRule):
    """WCAG 1.3.1 - Heading hierarchy should be logical."""

    rule_id = "heading-order"
    wcag_criterion = "1.3.1"
    wcag_level = "A"
    description = "Headings must follow a logical hierarchy"

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        headings = page_data.get("headings", [])

        if not headings:
            return issues

        # Check for missing h1
        has_h1 = any(h.get("level") == 1 for h in headings)
        if not has_h1:
            issues.append({
                "rule_id": self.rule_id,
                "wcag_criterion": self.wcag_criterion,
                "wcag_level": self.wcag_level,
                "severity": "major",
                "title": "Page missing h1 heading",
                "description": "The page does not have an h1 heading element.",
                "recommendation": "Add a single h1 element as the main page heading.",
                "detected_by": "rule",
            })

        # Check for skipped levels
        prev_level = 0
        for h in headings:
            level = h.get("level", 0)
            if level > prev_level + 1 and prev_level > 0:
                issues.append({
                    "rule_id": self.rule_id,
                    "wcag_criterion": self.wcag_criterion,
                    "wcag_level": self.wcag_level,
                    "severity": "minor",
                    "title": f"Heading level skipped from h{prev_level} to h{level}",
                    "description": f"Heading '{h.get('text', '')[:60]}' skips from level {prev_level} to {level}.",
                    "recommendation": "Ensure heading levels are sequential without gaps.",
                    "detected_by": "rule",
                })
            prev_level = level

        return issues


class LanguageRule(A11yRule):
    """WCAG 3.1.1 - Page language must be specified."""

    rule_id = "html-lang"
    wcag_criterion = "3.1.1"
    wcag_level = "A"
    description = "Page must have a valid lang attribute"

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        lang = page_data.get("lang", "")

        if not lang:
            issues.append({
                "rule_id": self.rule_id,
                "wcag_criterion": self.wcag_criterion,
                "wcag_level": self.wcag_level,
                "severity": "critical",
                "title": "Page language not specified",
                "description": "The <html> element is missing the lang attribute.",
                "recommendation": "Add a lang attribute to the <html> element (e.g., lang='zh-CN' or lang='en').",
                "detected_by": "rule",
            })

        return issues


class LandmarkRule(A11yRule):
    """WCAG 1.3.1 - Page should use ARIA landmarks."""

    rule_id = "landmark-structure"
    wcag_criterion = "1.3.1"
    wcag_level = "A"
    description = "Page should have proper landmark structure"

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        landmarks = page_data.get("landmarks", [])
        landmark_roles = {l.get("role", l.get("tag", "")) for l in landmarks}

        # Check for main landmark
        if "main" not in landmark_roles:
            issues.append({
                "rule_id": self.rule_id,
                "wcag_criterion": self.wcag_criterion,
                "wcag_level": self.wcag_level,
                "severity": "major",
                "title": "Missing main landmark",
                "description": "Page does not have a <main> element or role='main' landmark.",
                "recommendation": "Wrap the main content in a <main> element.",
                "detected_by": "rule",
            })

        # Check for navigation landmark
        if "navigation" not in landmark_roles and "nav" not in landmark_roles:
            issues.append({
                "rule_id": self.rule_id,
                "wcag_criterion": self.wcag_criterion,
                "wcag_level": self.wcag_level,
                "severity": "minor",
                "title": "Missing navigation landmark",
                "description": "Page does not have a <nav> element or role='navigation' landmark.",
                "recommendation": "Wrap navigation links in a <nav> element.",
                "detected_by": "rule",
            })

        return issues


class LinkTextRule(A11yRule):
    """WCAG 2.4.4 - Link text should be descriptive."""

    rule_id = "link-text"
    wcag_criterion = "2.4.4"
    wcag_level = "A"
    description = "Links must have descriptive text"

    GENERIC_LINK_TEXTS = {
        "click here", "here", "read more", "more", "learn more",
        "link", "click", "详情", "更多", "点击这里", "链接",
    }

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        for link in page_data.get("links", []):
            text = (link.get("text") or "").strip().lower()
            aria_label = link.get("aria_label") or ""

            if not text and not aria_label:
                issues.append({
                    "rule_id": self.rule_id,
                    "wcag_criterion": self.wcag_criterion,
                    "wcag_level": self.wcag_level,
                    "severity": "critical",
                    "title": "Link has no accessible text",
                    "description": f"Link to '{link.get('href', '')[:80]}' has no visible text or aria-label.",
                    "recommendation": "Add descriptive text content or an aria-label to the link.",
                    "detected_by": "rule",
                })
            elif text in self.GENERIC_LINK_TEXTS and not aria_label:
                issues.append({
                    "rule_id": self.rule_id,
                    "wcag_criterion": self.wcag_criterion,
                    "wcag_level": self.wcag_level,
                    "severity": "minor",
                    "title": "Link has generic text",
                    "description": f"Link text '{text}' is not descriptive. Users need to understand the link's purpose.",
                    "recommendation": "Replace generic text with descriptive text that indicates the link's destination.",
                    "detected_by": "rule",
                })

        return issues


# Register all rules
for rule_class in [
    ImageAltTextRule,
    EmptyAltTextRule,
    FormLabelRule,
    HeadingHierarchyRule,
    LanguageRule,
    LandmarkRule,
    LinkTextRule,
]:
    registry.register(rule_class())
