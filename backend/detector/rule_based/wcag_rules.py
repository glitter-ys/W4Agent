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


# ---------------------------------------------------------------------------
# AA-level rules
# ---------------------------------------------------------------------------


def _parse_rgb(color_str: str) -> tuple[int, int, int] | None:
    """Parse a CSS rgb/rgba color string into (r, g, b)."""
    m = re.match(r"rgba?\(\s*(\d+),\s*(\d+),\s*(\d+)", color_str)
    if m:
        return int(m.group(1)), int(m.group(2)), int(m.group(3))
    return None


def _relative_luminance(r: int, g: int, b: int) -> float:
    """Calculate relative luminance per WCAG 2.x definition."""
    def _channel(c: int) -> float:
        s = c / 255.0
        return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4
    return 0.2126 * _channel(r) + 0.7152 * _channel(g) + 0.0722 * _channel(b)


def _contrast_ratio(fg: tuple[int, int, int], bg: tuple[int, int, int]) -> float:
    """Calculate WCAG contrast ratio between two colors."""
    l1 = _relative_luminance(*fg)
    l2 = _relative_luminance(*bg)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


class ContrastRatioRule(A11yRule):
    """WCAG 1.4.3 - Contrast (Minimum): Text must have sufficient contrast."""

    rule_id = "color-contrast"
    wcag_criterion = "1.4.3"
    wcag_level = "AA"
    description = "Text must have a contrast ratio of at least 4.5:1 (3:1 for large text)"

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        for sample in page_data.get("text_samples", []):
            fg = _parse_rgb(sample.get("color", ""))
            bg = _parse_rgb(sample.get("background_color", ""))
            if not fg or not bg:
                continue

            ratio = _contrast_ratio(fg, bg)
            font_size_str = sample.get("font_size", "16px")
            font_size = float(re.sub(r"[^\d.]", "", font_size_str) or "16")
            font_weight = int(sample.get("font_weight", "400") or "400")
            is_large = font_size >= 24 or (font_size >= 18.66 and font_weight >= 700)
            min_ratio = 3.0 if is_large else 4.5

            if ratio < min_ratio:
                issues.append({
                    "rule_id": self.rule_id,
                    "wcag_criterion": self.wcag_criterion,
                    "wcag_level": self.wcag_level,
                    "severity": "critical" if ratio < 3.0 else "major",
                    "title": "Insufficient color contrast",
                    "description": (
                        f"Text '{sample.get('text', '')[:40]}' has contrast ratio {ratio:.2f}:1 "
                        f"(required: {min_ratio}:1). "
                        f"Foreground: {sample.get('color')}, Background: {sample.get('background_color')}."
                    ),
                    "recommendation": (
                        f"Increase the contrast ratio to at least {min_ratio}:1. "
                        "Darken the text or lighten the background."
                    ),
                    "element_selector": sample.get("selector", ""),
                    "detected_by": "rule",
                })
        return issues


class ResizeTextRule(A11yRule):
    """WCAG 1.4.4 - Resize text: viewport must not disable user scaling."""

    rule_id = "meta-viewport-scale"
    wcag_criterion = "1.4.4"
    wcag_level = "AA"
    description = "Viewport meta must not disable user scaling"

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        viewport = page_data.get("viewport_meta", "")
        if not viewport:
            return issues

        vp_lower = viewport.lower().replace(" ", "")
        if "user-scalable=no" in vp_lower or "user-scalable=0" in vp_lower:
            issues.append({
                "rule_id": self.rule_id,
                "wcag_criterion": self.wcag_criterion,
                "wcag_level": self.wcag_level,
                "severity": "critical",
                "title": "User scaling is disabled",
                "description": "The viewport meta tag contains 'user-scalable=no', preventing users from zooming.",
                "recommendation": "Remove 'user-scalable=no' or set it to 'yes' to allow users to zoom the page.",
                "element_selector": "meta[name='viewport']",
                "detected_by": "rule",
            })

        max_scale_match = re.search(r"maximum-scale=([0-9.]+)", vp_lower)
        if max_scale_match:
            max_scale = float(max_scale_match.group(1))
            if max_scale < 2.0:
                issues.append({
                    "rule_id": self.rule_id,
                    "wcag_criterion": self.wcag_criterion,
                    "wcag_level": self.wcag_level,
                    "severity": "major",
                    "title": "Maximum scale is too restrictive",
                    "description": f"The viewport meta tag sets maximum-scale={max_scale}, limiting zoom to {max_scale}x.",
                    "recommendation": "Set maximum-scale to at least 2.0, or remove the restriction entirely.",
                    "element_selector": "meta[name='viewport']",
                    "detected_by": "rule",
                })
        return issues


class PageTitleRule(A11yRule):
    """WCAG 2.4.2 - Page Titled: Pages must have descriptive titles."""

    rule_id = "page-title"
    wcag_criterion = "2.4.2"
    wcag_level = "A"
    description = "Pages must have descriptive titles"

    GENERIC_TITLES = {
        "untitled", "untitled document", "new page", "home",
        "无标题", "新页面", "document", "page",
    }

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        title = (page_data.get("title") or "").strip()

        if not title:
            issues.append({
                "rule_id": self.rule_id,
                "wcag_criterion": self.wcag_criterion,
                "wcag_level": self.wcag_level,
                "severity": "critical",
                "title": "Page has no title",
                "description": "The page is missing a <title> element.",
                "recommendation": "Add a descriptive <title> element that identifies the page's purpose.",
                "detected_by": "rule",
            })
        elif title.lower() in self.GENERIC_TITLES:
            issues.append({
                "rule_id": self.rule_id,
                "wcag_criterion": self.wcag_criterion,
                "wcag_level": self.wcag_level,
                "severity": "major",
                "title": "Page has a generic title",
                "description": f"Page title '{title}' is not descriptive.",
                "recommendation": "Use a title that describes the page content or purpose.",
                "detected_by": "rule",
            })
        return issues


class FocusVisibleRule(A11yRule):
    """WCAG 2.4.7 - Focus Visible: Interactive elements must have visible focus indicators."""

    rule_id = "focus-visible"
    wcag_criterion = "2.4.7"
    wcag_level = "AA"
    description = "Interactive elements must have visible focus indicators"

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        for el in page_data.get("focus_styles", []):
            if el.get("has_outline_none"):
                issues.append({
                    "rule_id": self.rule_id,
                    "wcag_criterion": self.wcag_criterion,
                    "wcag_level": self.wcag_level,
                    "severity": "major",
                    "title": "Focus indicator removed",
                    "description": (
                        f"Element <{el.get('tag', '')}> '{el.get('text', '')[:40]}' "
                        "has outline:none, which removes the visible focus indicator."
                    ),
                    "recommendation": (
                        "Do not remove the default focus outline. If customizing, ensure a visible "
                        "alternative focus style (e.g., box-shadow, border, or custom outline)."
                    ),
                    "detected_by": "rule",
                })
        return issues


class InputPurposeRule(A11yRule):
    """WCAG 1.3.5 - Identify Input Purpose: Inputs for personal data should have autocomplete."""

    rule_id = "input-autocomplete"
    wcag_criterion = "1.3.5"
    wcag_level = "AA"
    description = "Inputs collecting personal data must identify their purpose via autocomplete"

    # Maps common input name patterns to expected autocomplete values
    PURPOSE_PATTERNS = {
        r"(?:first|given).?name": "given-name",
        r"(?:last|family|sur).?name": "family-name",
        r"(?:full.?)?name": "name",
        r"e.?mail": "email",
        r"(?:tele)?phone|tel|mobile": "tel",
        r"(?:zip|postal).?code": "postal-code",
        r"street|address.?line": "street-address",
        r"city|town": "address-level2",
        r"state|province|region": "address-level1",
        r"country": "country-name",
        r"(?:user).?name|login": "username",
        r"pass(?:word)?": "current-password",
        r"new.?pass(?:word)?": "new-password",
        r"(?:cc|card).?num": "cc-number",
        r"(?:cc|card).?name": "cc-name",
        r"(?:cc|card).?exp": "cc-exp",
        r"bday|birth.?d(?:ay|ate)": "bday",
        r"organ(?:ization|isation)|company": "organization",
    }

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        for inp in page_data.get("autocomplete_inputs", []):
            autocomplete = inp.get("autocomplete", "").strip()
            if autocomplete and autocomplete != "off":
                continue

            name = (inp.get("name") or inp.get("id") or "").lower()
            placeholder = (inp.get("placeholder") or "").lower()
            label = (inp.get("aria_label") or "").lower()
            combined = f"{name} {placeholder} {label}"

            for pattern, expected in self.PURPOSE_PATTERNS.items():
                if re.search(pattern, combined):
                    issues.append({
                        "rule_id": self.rule_id,
                        "wcag_criterion": self.wcag_criterion,
                        "wcag_level": self.wcag_level,
                        "severity": "major",
                        "title": "Input missing autocomplete attribute",
                        "description": (
                            f"Input '{name or inp.get('id', 'unknown')}' appears to collect personal data "
                            f"but lacks an appropriate autocomplete attribute."
                        ),
                        "recommendation": f"Add autocomplete=\"{expected}\" to this input field.",
                        "element_selector": f"input[name='{inp.get('name', '')}']",
                        "detected_by": "rule",
                    })
                    break
        return issues


class TabindexRule(A11yRule):
    """WCAG 2.4.3 - Focus Order: Positive tabindex disrupts natural focus order."""

    rule_id = "tabindex-positive"
    wcag_criterion = "2.4.3"
    wcag_level = "A"
    description = "Elements should not use positive tabindex values"

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        for el in page_data.get("tabindex_elements", []):
            tabindex = el.get("tabindex", 0)
            if tabindex > 0:
                issues.append({
                    "rule_id": self.rule_id,
                    "wcag_criterion": self.wcag_criterion,
                    "wcag_level": self.wcag_level,
                    "severity": "major",
                    "title": "Element uses positive tabindex",
                    "description": (
                        f"Element <{el.get('tag', '')}> '{el.get('text', '')[:40]}' has "
                        f"tabindex={tabindex}, which disrupts the natural tab order."
                    ),
                    "recommendation": "Use tabindex='0' to add elements to natural tab order, or tabindex='-1' for programmatic focus only.",
                    "detected_by": "rule",
                })
        return issues


class DuplicateIdRule(A11yRule):
    """WCAG 4.1.1 - Parsing: IDs must be unique in the document."""

    rule_id = "duplicate-id"
    wcag_criterion = "4.1.1"
    wcag_level = "A"
    description = "Element IDs must be unique"

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        for dup in page_data.get("duplicate_ids", []):
            issues.append({
                "rule_id": self.rule_id,
                "wcag_criterion": self.wcag_criterion,
                "wcag_level": self.wcag_level,
                "severity": "critical",
                "title": "Duplicate element ID",
                "description": f"ID '{dup.get('id')}' appears {dup.get('count')} times. IDs must be unique.",
                "recommendation": "Ensure each id attribute value is unique within the page.",
                "element_selector": f"[id='{dup.get('id', '')}']",
                "detected_by": "rule",
            })
        return issues


class ButtonNameRule(A11yRule):
    """WCAG 4.1.2 - Name, Role, Value: Buttons must have accessible names."""

    rule_id = "button-name"
    wcag_criterion = "4.1.2"
    wcag_level = "A"
    description = "Buttons must have discernible accessible names"

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        for el in page_data.get("interactive_elements", []):
            tag = el.get("tag", "")
            text = (el.get("text") or "").strip()
            aria_label = el.get("aria_label") or ""

            if not text and not aria_label:
                issues.append({
                    "rule_id": self.rule_id,
                    "wcag_criterion": self.wcag_criterion,
                    "wcag_level": self.wcag_level,
                    "severity": "critical",
                    "title": "Button has no accessible name",
                    "description": f"A <{tag}> element has no text content or aria-label.",
                    "recommendation": "Add text content, aria-label, or aria-labelledby to the button.",
                    "detected_by": "rule",
                })
        return issues


class LanguageValidRule(A11yRule):
    """WCAG 3.1.1 - Language of Page: lang attribute must use a valid BCP 47 tag."""

    rule_id = "html-lang-valid"
    wcag_criterion = "3.1.1"
    wcag_level = "A"
    description = "The lang attribute must contain a valid language code"

    # Common valid BCP 47 primary subtags
    VALID_LANGS = {
        "af", "am", "ar", "az", "be", "bg", "bn", "bs", "ca", "cs", "cy", "da",
        "de", "el", "en", "es", "et", "eu", "fa", "fi", "fil", "fr", "ga", "gl",
        "gu", "he", "hi", "hr", "hu", "hy", "id", "is", "it", "ja", "jv", "ka",
        "kk", "km", "kn", "ko", "ky", "lo", "lt", "lv", "mk", "ml", "mn", "mr",
        "ms", "my", "nb", "ne", "nl", "nn", "no", "pa", "pl", "ps", "pt", "ro",
        "ru", "sd", "si", "sk", "sl", "sq", "sr", "sv", "sw", "ta", "te", "th",
        "tk", "tl", "tr", "uk", "ur", "uz", "vi", "zh", "zu",
    }

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        lang = page_data.get("lang", "")
        if not lang:
            return issues  # Missing lang is caught by LanguageRule

        primary = lang.split("-")[0].lower().strip()
        if primary and primary not in self.VALID_LANGS:
            issues.append({
                "rule_id": self.rule_id,
                "wcag_criterion": self.wcag_criterion,
                "wcag_level": self.wcag_level,
                "severity": "major",
                "title": "Invalid language code",
                "description": f"The lang attribute value '{lang}' does not appear to be a valid BCP 47 language tag.",
                "recommendation": "Use a valid BCP 47 language tag (e.g., 'en', 'zh-CN', 'ja').",
                "element_selector": "html",
                "detected_by": "rule",
            })
        return issues


class LanguageOfPartsRule(A11yRule):
    """WCAG 3.1.2 - Language of Parts: Content in a different language should be marked."""

    rule_id = "lang-parts-valid"
    wcag_criterion = "3.1.2"
    wcag_level = "AA"
    description = "Elements with a lang attribute must use valid language codes"

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        for part in page_data.get("lang_parts", []):
            lang = part.get("lang", "")
            if not lang:
                continue
            primary = lang.split("-")[0].lower().strip()
            if primary and primary not in LanguageValidRule.VALID_LANGS:
                issues.append({
                    "rule_id": self.rule_id,
                    "wcag_criterion": self.wcag_criterion,
                    "wcag_level": self.wcag_level,
                    "severity": "minor",
                    "title": "Invalid language code on element",
                    "description": (
                        f"Element <{part.get('tag', '')}> has lang='{lang}' "
                        "which is not a valid BCP 47 tag."
                    ),
                    "recommendation": "Use a valid BCP 47 language subtag for the lang attribute.",
                    "detected_by": "rule",
                })
        return issues


class TextSpacingRule(A11yRule):
    """WCAG 1.4.12 - Text Spacing: Check that text spacing is not overly restricted."""

    rule_id = "text-spacing"
    wcag_criterion = "1.4.12"
    wcag_level = "AA"
    description = "Text spacing should allow user customization without loss of content"

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        html = page_data.get("html", "")
        if not html:
            return issues

        # Detect !important declarations that lock down text-spacing properties
        important_patterns = [
            (r"line-height\s*:\s*[^;]*!important", "line-height"),
            (r"letter-spacing\s*:\s*[^;]*!important", "letter-spacing"),
            (r"word-spacing\s*:\s*[^;]*!important", "word-spacing"),
        ]
        for pattern, prop in important_patterns:
            if re.search(pattern, html, re.IGNORECASE):
                issues.append({
                    "rule_id": self.rule_id,
                    "wcag_criterion": self.wcag_criterion,
                    "wcag_level": self.wcag_level,
                    "severity": "major",
                    "title": f"Text spacing property '{prop}' uses !important",
                    "description": (
                        f"The CSS property '{prop}' is set with !important, "
                        "which may prevent users from adjusting text spacing."
                    ),
                    "recommendation": f"Avoid using !important for {prop}. Allow user stylesheets to override spacing.",
                    "detected_by": "rule",
                })
        return issues


class NonTextContrastRule(A11yRule):
    """WCAG 1.4.11 - Non-text Contrast: UI components must have 3:1 contrast."""

    rule_id = "non-text-contrast"
    wcag_criterion = "1.4.11"
    wcag_level = "AA"
    description = "UI components and graphical objects must have 3:1 contrast ratio"

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        for el in page_data.get("focus_styles", []):
            outline_color = _parse_rgb(el.get("outline_color", ""))
            if not outline_color:
                continue
            # Check contrast of the focus indicator against white background
            bg = (255, 255, 255)
            ratio = _contrast_ratio(outline_color, bg)
            if ratio < 3.0 and not el.get("has_outline_none"):
                issues.append({
                    "rule_id": self.rule_id,
                    "wcag_criterion": self.wcag_criterion,
                    "wcag_level": self.wcag_level,
                    "severity": "major",
                    "title": "Low contrast focus indicator",
                    "description": (
                        f"Element <{el.get('tag', '')}> '{el.get('text', '')[:40]}' "
                        f"has a focus outline with contrast ratio {ratio:.2f}:1 against white (required: 3:1)."
                    ),
                    "recommendation": "Use a focus indicator color with at least 3:1 contrast against adjacent colors.",
                    "detected_by": "rule",
                })
        return issues


class AriaLiveRegionRule(A11yRule):
    """WCAG 4.1.3 - Status Messages: Dynamic status messages must use ARIA live regions."""

    rule_id = "aria-live-region"
    wcag_criterion = "4.1.3"
    wcag_level = "AA"
    description = "Status messages must be programmatically determinable via ARIA live regions"

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        live_regions = page_data.get("aria_live_regions", [])

        for region in live_regions:
            role = region.get("role", "")
            aria_live = region.get("aria_live", "")

            # alert role should be aria-live="assertive"
            if role == "alert" and aria_live and aria_live != "assertive":
                issues.append({
                    "rule_id": self.rule_id,
                    "wcag_criterion": self.wcag_criterion,
                    "wcag_level": self.wcag_level,
                    "severity": "minor",
                    "title": "Alert region with wrong aria-live value",
                    "description": (
                        f"Element with role='alert' has aria-live='{aria_live}'. "
                        "Alerts should use assertive politeness."
                    ),
                    "recommendation": "Use aria-live='assertive' with role='alert', or remove the explicit aria-live to use the role's default.",
                    "detected_by": "rule",
                })

            # status role should be aria-live="polite"
            if role == "status" and aria_live and aria_live != "polite":
                issues.append({
                    "rule_id": self.rule_id,
                    "wcag_criterion": self.wcag_criterion,
                    "wcag_level": self.wcag_level,
                    "severity": "minor",
                    "title": "Status region with wrong aria-live value",
                    "description": (
                        f"Element with role='status' has aria-live='{aria_live}'. "
                        "Status messages should use polite politeness."
                    ),
                    "recommendation": "Use aria-live='polite' with role='status', or remove the explicit aria-live to use the role's default.",
                    "detected_by": "rule",
                })

            # aria-live="off" on a live-region role is likely a mistake
            if aria_live == "off" and role in ("alert", "status", "log"):
                issues.append({
                    "rule_id": self.rule_id,
                    "wcag_criterion": self.wcag_criterion,
                    "wcag_level": self.wcag_level,
                    "severity": "major",
                    "title": "Live region disabled",
                    "description": (
                        f"Element with role='{role}' has aria-live='off', "
                        "which silences announcements to assistive technology."
                    ),
                    "recommendation": f"Remove aria-live='off' to allow the '{role}' role's default live behavior.",
                    "detected_by": "rule",
                })
        return issues


class FormErrorIdentificationRule(A11yRule):
    """WCAG 3.3.1 - Error Identification: Required inputs must be properly indicated."""

    rule_id = "form-required-indicator"
    wcag_criterion = "3.3.1"
    wcag_level = "A"
    description = "Required form fields must be clearly identified"

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        for form in page_data.get("forms", []):
            for inp in form.get("inputs", []):
                if inp.get("type") in ("hidden", "submit", "button", "reset", "image"):
                    continue
                if inp.get("required"):
                    has_label = inp.get("has_label", False)
                    has_aria = bool(inp.get("aria_label"))
                    if not has_label and not has_aria:
                        issues.append({
                            "rule_id": self.rule_id,
                            "wcag_criterion": self.wcag_criterion,
                            "wcag_level": self.wcag_level,
                            "severity": "major",
                            "title": "Required input not clearly identified",
                            "description": (
                                f"Required input '{inp.get('name', 'unnamed')}' (type: {inp.get('type')}) "
                                "has no label to indicate it is required."
                            ),
                            "recommendation": (
                                "Add a visible label that indicates the field is required "
                                "(e.g., 'Name (required)' or use aria-required='true')."
                            ),
                            "element_selector": f"input[name='{inp.get('name', '')}']",
                            "detected_by": "rule",
                        })
        return issues


class MultipleWaysRule(A11yRule):
    """WCAG 2.4.5 - Multiple Ways: Sites should provide multiple ways to find pages."""

    rule_id = "multiple-ways"
    wcag_criterion = "2.4.5"
    wcag_level = "AA"
    description = "Websites should provide more than one way to locate a page (search, sitemap, navigation)"

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        landmarks = page_data.get("landmarks", [])
        landmark_roles = {l.get("role", l.get("tag", "")) for l in landmarks}
        html = page_data.get("html", "").lower()

        has_nav = "navigation" in landmark_roles or "nav" in landmark_roles
        has_search = (
            "search" in landmark_roles
            or 'role="search"' in html
            or 'type="search"' in html
            or "search" in html[:5000]
        )
        has_sitemap = "sitemap" in html

        ways_count = sum([has_nav, has_search, has_sitemap])
        if ways_count < 1:
            issues.append({
                "rule_id": self.rule_id,
                "wcag_criterion": self.wcag_criterion,
                "wcag_level": self.wcag_level,
                "severity": "minor",
                "title": "Page may lack multiple ways to navigate",
                "description": "No navigation, search, or sitemap link was found on the page.",
                "recommendation": (
                    "Provide at least two of: site navigation, search functionality, "
                    "or a site map to help users find content."
                ),
                "detected_by": "rule",
            })
        return issues


class LabelInNameRule(A11yRule):
    """WCAG 2.5.3 - Label in Name: Accessible name must contain the visible label."""

    rule_id = "label-in-name"
    wcag_criterion = "2.5.3"
    wcag_level = "A"
    description = "An element's accessible name must contain its visible text label"

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        for el in page_data.get("interactive_elements", []):
            text = (el.get("text") or "").strip().lower()
            aria_label = (el.get("aria_label") or "").strip().lower()
            if text and aria_label and text not in aria_label:
                issues.append({
                    "rule_id": self.rule_id,
                    "wcag_criterion": self.wcag_criterion,
                    "wcag_level": self.wcag_level,
                    "severity": "major",
                    "title": "Accessible name does not contain visible text",
                    "description": (
                        f"Element <{el.get('tag', '')}> has visible text '{text[:40]}' "
                        f"but aria-label '{aria_label[:40]}' does not contain it."
                    ),
                    "recommendation": (
                        "Ensure the aria-label includes the visible text. "
                        "For example, if the button says 'Search', the aria-label "
                        "should contain 'Search' (e.g., 'Search products')."
                    ),
                    "detected_by": "rule",
                })

        # Also check links
        for link in page_data.get("links", []):
            text = (link.get("text") or "").strip().lower()
            aria_label = (link.get("aria_label") or "").strip().lower()
            if text and aria_label and text not in aria_label:
                issues.append({
                    "rule_id": self.rule_id,
                    "wcag_criterion": self.wcag_criterion,
                    "wcag_level": self.wcag_level,
                    "severity": "major",
                    "title": "Link accessible name does not contain visible text",
                    "description": (
                        f"Link with visible text '{text[:40]}' has aria-label "
                        f"'{aria_label[:40]}' which does not contain the visible text."
                    ),
                    "recommendation": "Ensure the aria-label includes the visible link text.",
                    "detected_by": "rule",
                })
        return issues


class ImageLongAltRule(A11yRule):
    """Check for excessively long alt text that should use longdesc or aria-describedby."""

    rule_id = "img-alt-long"
    wcag_criterion = "1.1.1"
    wcag_level = "AA"
    description = "Image alt text should be concise; long descriptions should use other mechanisms"

    MAX_ALT_LENGTH = 150

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        for img in page_data.get("images", []):
            alt = img.get("alt") or ""
            if len(alt) > self.MAX_ALT_LENGTH:
                issues.append({
                    "rule_id": self.rule_id,
                    "wcag_criterion": self.wcag_criterion,
                    "wcag_level": self.wcag_level,
                    "severity": "minor",
                    "title": "Image alt text is excessively long",
                    "description": (
                        f"Image alt text is {len(alt)} characters long (recommended max: {self.MAX_ALT_LENGTH}). "
                        f"Alt text: '{alt[:60]}...'"
                    ),
                    "recommendation": (
                        "Shorten the alt text and use aria-describedby or a visible "
                        "text description for detailed information."
                    ),
                    "element_selector": f"img[src*='{img.get('src', '')[:50]}']",
                    "detected_by": "rule",
                })
        return issues


class AutoplayMediaRule(A11yRule):
    """WCAG 1.4.2 - Audio Control: Auto-playing media must have controls."""

    rule_id = "no-autoplay"
    wcag_criterion = "1.4.2"
    wcag_level = "A"
    description = "Audio/video that auto-plays must have a mechanism to pause or stop"

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        html = page_data.get("html", "")
        if not html:
            return issues

        # Check for autoplay in video/audio tags
        autoplay_pattern = r"<(?:video|audio)[^>]*\bautoplay\b[^>]*>"
        matches = re.findall(autoplay_pattern, html, re.IGNORECASE)
        for match in matches:
            has_muted = "muted" in match.lower()
            if not has_muted:
                issues.append({
                    "rule_id": self.rule_id,
                    "wcag_criterion": self.wcag_criterion,
                    "wcag_level": self.wcag_level,
                    "severity": "critical",
                    "title": "Media auto-plays with sound",
                    "description": "A video or audio element has autoplay enabled without being muted.",
                    "recommendation": (
                        "Remove autoplay, add the 'muted' attribute, or provide a visible "
                        "mechanism to pause/stop and control volume."
                    ),
                    "detected_by": "rule",
                })
        return issues


class LinkTargetBlankRule(A11yRule):
    """Links opening in new windows should warn users."""

    rule_id = "link-target-blank"
    wcag_criterion = "3.2.5"
    wcag_level = "AAA"
    description = "Links that open in new windows should indicate this to users"

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        for link in page_data.get("links", []):
            target = (link.get("target") or "").strip()
            if target == "_blank":
                text = (link.get("text") or "").lower()
                aria_label = (link.get("aria_label") or "").lower()
                combined = text + " " + aria_label
                warns = any(w in combined for w in ("new window", "new tab", "外部链接", "新窗口", "新标签"))
                if not warns:
                    issues.append({
                        "rule_id": self.rule_id,
                        "wcag_criterion": self.wcag_criterion,
                        "wcag_level": self.wcag_level,
                        "severity": "minor",
                        "title": "Link opens in new window without warning",
                        "description": (
                            f"Link '{(link.get('text') or '')[:40]}' opens in a new window (target='_blank') "
                            "without indicating this to the user."
                        ),
                        "recommendation": "Add visual and/or textual indication that the link opens in a new window (e.g., '(opens in new tab)').",
                        "detected_by": "rule",
                    })
        return issues


# Register all rules
for rule_class in [
    # Level A rules
    ImageAltTextRule,
    EmptyAltTextRule,
    FormLabelRule,
    HeadingHierarchyRule,
    LanguageRule,
    LanguageValidRule,
    LandmarkRule,
    LinkTextRule,
    PageTitleRule,
    TabindexRule,
    DuplicateIdRule,
    ButtonNameRule,
    LabelInNameRule,
    AutoplayMediaRule,
    FormErrorIdentificationRule,
    # Level AA rules
    ContrastRatioRule,
    ResizeTextRule,
    FocusVisibleRule,
    InputPurposeRule,
    LanguageOfPartsRule,
    TextSpacingRule,
    NonTextContrastRule,
    AriaLiveRegionRule,
    MultipleWaysRule,
    ImageLongAltRule,
    # Level AAA rules
    LinkTargetBlankRule,
]:
    registry.register(rule_class())
