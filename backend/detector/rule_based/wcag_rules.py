from __future__ import annotations

import re
from typing import Any

from detector.rule_based.rule_registry import A11yRule, registry


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
            aria_labelledby = link.get("aria_labelledby") or ""
            title = link.get("title") or ""

            has_name = text or aria_label or aria_labelledby or title

            if not has_name:
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
    """Parse a CSS rgb/rgba color string into (r, g, b). Returns None for transparent colors."""
    m = re.match(r"rgba?\(\s*(\d+),\s*(\d+),\s*(\d+)(?:,\s*([0-9.]+))?\)", color_str)
    if m:
        # If alpha channel is present and zero, treat as transparent (skip)
        alpha = m.group(4)
        if alpha is not None and float(alpha) == 0:
            return None
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
            aria_labelledby = el.get("aria_labelledby") or ""
            title = el.get("title") or ""
            value = el.get("value") or ""

            has_name = text or aria_label or aria_labelledby or title or value

            if not has_name:
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


# ---------------------------------------------------------------------------
# New rules – additional axe-core / WCAG coverage
# ---------------------------------------------------------------------------


class AreaAltRule(A11yRule):
    """WCAG 1.1.1 - <area> elements must have alternative text."""

    rule_id = "area-alt"
    wcag_criterion = "1.1.1"
    wcag_level = "A"
    description = "<area> elements must have alternative text"

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        html = page_data.get("html", "")
        if not html:
            return issues
        for m in re.finditer(r"<area\b([^>]*)>", html, re.IGNORECASE):
            attrs = m.group(1)
            has_alt = re.search(r'\balt\s*=\s*["\'][^"\']+["\']', attrs, re.IGNORECASE)
            has_aria = re.search(r'\baria-label\s*=\s*["\'][^"\']+["\']', attrs, re.IGNORECASE)
            has_aria_labelledby = re.search(r'\baria-labelledby\s*=', attrs, re.IGNORECASE)
            if not has_alt and not has_aria and not has_aria_labelledby:
                href = ""
                href_m = re.search(r'\bhref\s*=\s*["\']([^"\']*)["\']', attrs, re.IGNORECASE)
                if href_m:
                    href = href_m.group(1)[:80]
                issues.append({
                    "rule_id": self.rule_id,
                    "wcag_criterion": self.wcag_criterion,
                    "wcag_level": self.wcag_level,
                    "severity": "critical",
                    "title": "<area> element missing alt text",
                    "description": f"An <area> element (href='{href}') has no alt, aria-label, or aria-labelledby attribute.",
                    "recommendation": "Add an alt attribute that describes the area's purpose.",
                    "element_selector": f"area[href='{href}']" if href else "area",
                    "detected_by": "rule",
                })
        return issues


class AriaAllowedAttrRule(A11yRule):
    """WCAG 4.1.2 - ARIA attributes must be compatible with the element's role."""

    rule_id = "aria-allowed-attr"
    wcag_criterion = "4.1.2"
    wcag_level = "A"
    description = "ARIA attributes must be compatible with the element's role"

    # Mapping of roles to their allowed ARIA attributes (subset of most common)
    ROLE_ALLOWED_ATTRS: dict[str, set[str]] = {
        "alert": {"aria-atomic", "aria-busy", "aria-controls", "aria-describedby", "aria-details",
                  "aria-flowto", "aria-label", "aria-labelledby", "aria-live", "aria-owns",
                  "aria-relevant", "aria-roledescription"},
        "button": {"aria-controls", "aria-describedby", "aria-details", "aria-disabled",
                   "aria-expanded", "aria-flowto", "aria-haspopup", "aria-label",
                   "aria-labelledby", "aria-owns", "aria-pressed", "aria-roledescription"},
        "checkbox": {"aria-checked", "aria-controls", "aria-describedby", "aria-details",
                     "aria-disabled", "aria-flowto", "aria-label", "aria-labelledby",
                     "aria-owns", "aria-readonly", "aria-required", "aria-roledescription"},
        "img": {"aria-describedby", "aria-details", "aria-flowto", "aria-label",
                "aria-labelledby", "aria-roledescription"},
        "link": {"aria-controls", "aria-describedby", "aria-details", "aria-disabled",
                 "aria-expanded", "aria-flowto", "aria-haspopup", "aria-label",
                 "aria-labelledby", "aria-owns", "aria-roledescription"},
        "presentation": set(),
        "none": set(),
    }

    # Global ARIA attributes allowed on any role
    GLOBAL_ATTRS = {
        "aria-atomic", "aria-busy", "aria-controls", "aria-current", "aria-describedby",
        "aria-details", "aria-disabled", "aria-dropeffect", "aria-flowto", "aria-grabbed",
        "aria-hidden", "aria-keyshortcuts", "aria-label", "aria-labelledby", "aria-live",
        "aria-owns", "aria-relevant", "aria-roledescription",
    }

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        for el in page_data.get("aria_elements", []):
            role = (el.get("role") or "").strip().lower()
            if not role or role not in self.ROLE_ALLOWED_ATTRS:
                continue
            allowed = self.ROLE_ALLOWED_ATTRS[role] | self.GLOBAL_ATTRS
            for attr_name in el.get("aria_attrs", []):
                if attr_name.startswith("aria-") and attr_name not in allowed:
                    issues.append({
                        "rule_id": self.rule_id,
                        "wcag_criterion": self.wcag_criterion,
                        "wcag_level": self.wcag_level,
                        "severity": "critical",
                        "title": f"ARIA attribute not allowed on role '{role}'",
                        "description": (
                            f"Element with role='{role}' has attribute '{attr_name}' "
                            "which is not allowed for this role."
                        ),
                        "recommendation": f"Remove '{attr_name}' or change the element's role to one that supports it.",
                        "element_selector": el.get("selector", ""),
                        "detected_by": "rule",
                    })
        return issues


class AriaHiddenFocusRule(A11yRule):
    """WCAG 4.1.2 - aria-hidden elements must not be focusable or contain focusable elements."""

    rule_id = "aria-hidden-focus"
    wcag_criterion = "4.1.2"
    wcag_level = "A"
    description = "aria-hidden elements must not be focusable or contain focusable elements"

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        for el in page_data.get("aria_hidden_focusable", []):
            issues.append({
                "rule_id": self.rule_id,
                "wcag_criterion": self.wcag_criterion,
                "wcag_level": self.wcag_level,
                "severity": "major",
                "title": "Focusable element inside aria-hidden",
                "description": (
                    f"Element <{el.get('tag', '')}>'{el.get('text', '')[:40]}' "
                    "is focusable but is contained within or has aria-hidden='true'. "
                    "Screen readers will not announce this element."
                ),
                "recommendation": (
                    "Remove aria-hidden='true' from the element or its ancestors, "
                    "or set tabindex='-1' to make it not focusable."
                ),
                "element_selector": el.get("selector", ""),
                "detected_by": "rule",
            })
        return issues


class AriaRequiredAttrRule(A11yRule):
    """WCAG 4.1.2 - ARIA roles must include all required attributes."""

    rule_id = "aria-required-attr"
    wcag_criterion = "4.1.2"
    wcag_level = "A"
    description = "ARIA roles must include all required attributes"

    ROLE_REQUIRED_ATTRS: dict[str, list[str]] = {
        "checkbox": ["aria-checked"],
        "combobox": ["aria-expanded"],
        "heading": ["aria-level"],
        "meter": ["aria-valuenow"],
        "option": ["aria-selected"],
        "radio": ["aria-checked"],
        "scrollbar": ["aria-controls", "aria-valuenow"],
        "separator": ["aria-valuenow"],  # when focusable
        "slider": ["aria-valuenow"],
        "switch": ["aria-checked"],
    }

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        for el in page_data.get("aria_elements", []):
            role = (el.get("role") or "").strip().lower()
            required = self.ROLE_REQUIRED_ATTRS.get(role)
            if not required:
                continue
            present_attrs = set(el.get("aria_attrs", []))
            for attr in required:
                if attr not in present_attrs:
                    issues.append({
                        "rule_id": self.rule_id,
                        "wcag_criterion": self.wcag_criterion,
                        "wcag_level": self.wcag_level,
                        "severity": "critical",
                        "title": f"Missing required ARIA attribute for role '{role}'",
                        "description": (
                            f"Element with role='{role}' is missing required attribute '{attr}'."
                        ),
                        "recommendation": f"Add the required attribute '{attr}' to the element with role='{role}'.",
                        "element_selector": el.get("selector", ""),
                        "detected_by": "rule",
                    })
        return issues


class AriaRequiredChildrenRule(A11yRule):
    """WCAG 4.1.2 - Certain ARIA roles must contain required child roles."""

    rule_id = "aria-required-children"
    wcag_criterion = "4.1.2"
    wcag_level = "A"
    description = "ARIA roles must contain required child roles"

    ROLE_REQUIRED_CHILDREN: dict[str, list[str]] = {
        "list": ["listitem"],
        "listbox": ["option"],
        "menu": ["menuitem", "menuitemcheckbox", "menuitemradio"],
        "menubar": ["menuitem", "menuitemcheckbox", "menuitemradio"],
        "radiogroup": ["radio"],
        "tablist": ["tab"],
        "tree": ["treeitem"],
        "grid": ["row", "rowgroup"],
        "table": ["row", "rowgroup"],
        "row": ["cell", "columnheader", "gridcell", "rowheader"],
    }

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        for el in page_data.get("aria_elements", []):
            role = (el.get("role") or "").strip().lower()
            required_children = self.ROLE_REQUIRED_CHILDREN.get(role)
            if not required_children:
                continue
            child_roles = set(el.get("child_roles", []))
            if not child_roles & set(required_children):
                issues.append({
                    "rule_id": self.rule_id,
                    "wcag_criterion": self.wcag_criterion,
                    "wcag_level": self.wcag_level,
                    "severity": "critical",
                    "title": f"Role '{role}' missing required child roles",
                    "description": (
                        f"Element with role='{role}' must contain at least one child "
                        f"with role: {', '.join(required_children)}."
                    ),
                    "recommendation": f"Add child elements with one of the required roles: {', '.join(required_children)}.",
                    "element_selector": el.get("selector", ""),
                    "detected_by": "rule",
                })
        return issues


class AriaRequiredParentRule(A11yRule):
    """WCAG 4.1.2 - Certain ARIA roles must be contained in required parent roles."""

    rule_id = "aria-required-parent"
    wcag_criterion = "4.1.2"
    wcag_level = "A"
    description = "ARIA roles must be contained within required parent roles"

    ROLE_REQUIRED_PARENT: dict[str, list[str]] = {
        "listitem": ["list"],
        "option": ["listbox"],
        "menuitem": ["menu", "menubar"],
        "menuitemcheckbox": ["menu", "menubar"],
        "menuitemradio": ["menu", "menubar"],
        "tab": ["tablist"],
        "treeitem": ["tree", "group"],
        "cell": ["row"],
        "columnheader": ["row"],
        "gridcell": ["row"],
        "rowheader": ["row"],
        "row": ["grid", "table", "treegrid", "rowgroup"],
    }

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        for el in page_data.get("aria_elements", []):
            role = (el.get("role") or "").strip().lower()
            required_parents = self.ROLE_REQUIRED_PARENT.get(role)
            if not required_parents:
                continue
            parent_role = (el.get("parent_role") or "").strip().lower()
            if parent_role not in required_parents:
                issues.append({
                    "rule_id": self.rule_id,
                    "wcag_criterion": self.wcag_criterion,
                    "wcag_level": self.wcag_level,
                    "severity": "critical",
                    "title": f"Role '{role}' not inside required parent",
                    "description": (
                        f"Element with role='{role}' must be contained in an element "
                        f"with role: {', '.join(required_parents)}."
                    ),
                    "recommendation": f"Place this element inside a parent with one of the required roles: {', '.join(required_parents)}.",
                    "element_selector": el.get("selector", ""),
                    "detected_by": "rule",
                })
        return issues


class AriaRolesRule(A11yRule):
    """WCAG 4.1.2 - role attribute values must be valid."""

    rule_id = "aria-roles"
    wcag_criterion = "4.1.2"
    wcag_level = "A"
    description = "role attribute values must be valid ARIA roles"

    VALID_ROLES = {
        "alert", "alertdialog", "application", "article", "banner", "blockquote",
        "button", "caption", "cell", "checkbox", "code", "columnheader", "combobox",
        "complementary", "contentinfo", "definition", "deletion", "dialog", "directory",
        "document", "emphasis", "feed", "figure", "form", "generic", "grid", "gridcell",
        "group", "heading", "img", "insertion", "link", "list", "listbox", "listitem",
        "log", "main", "marquee", "math", "meter", "menu", "menubar", "menuitem",
        "menuitemcheckbox", "menuitemradio", "navigation", "none", "note", "option",
        "paragraph", "presentation", "progressbar", "radio", "radiogroup", "region",
        "row", "rowgroup", "rowheader", "scrollbar", "search", "searchbox", "separator",
        "slider", "spinbutton", "status", "strong", "subscript", "superscript", "switch",
        "tab", "table", "tablist", "tabpanel", "term", "textbox", "time", "timer",
        "toolbar", "tooltip", "tree", "treegrid", "treeitem",
    }

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        for el in page_data.get("aria_elements", []):
            role_str = (el.get("role") or "").strip()
            if not role_str:
                continue
            for role in role_str.split():
                if role.lower() not in self.VALID_ROLES:
                    issues.append({
                        "rule_id": self.rule_id,
                        "wcag_criterion": self.wcag_criterion,
                        "wcag_level": self.wcag_level,
                        "severity": "critical",
                        "title": f"Invalid ARIA role '{role}'",
                        "description": f"The role '{role}' is not a valid WAI-ARIA role.",
                        "recommendation": "Use a valid ARIA role value. See WAI-ARIA specification for the full list.",
                        "element_selector": el.get("selector", ""),
                        "detected_by": "rule",
                    })
        return issues


class AriaValidAttrRule(A11yRule):
    """WCAG 4.1.2 - ARIA attribute names must be valid."""

    rule_id = "aria-valid-attr"
    wcag_criterion = "4.1.2"
    wcag_level = "A"
    description = "ARIA attribute names must be valid"

    VALID_ARIA_ATTRS = {
        "aria-activedescendant", "aria-atomic", "aria-autocomplete", "aria-braillelabel",
        "aria-brailleroledescription", "aria-busy", "aria-checked", "aria-colcount",
        "aria-colindex", "aria-colindextext", "aria-colspan", "aria-controls",
        "aria-current", "aria-describedby", "aria-description", "aria-details",
        "aria-disabled", "aria-dropeffect", "aria-errormessage", "aria-expanded",
        "aria-flowto", "aria-grabbed", "aria-haspopup", "aria-hidden", "aria-invalid",
        "aria-keyshortcuts", "aria-label", "aria-labelledby", "aria-level", "aria-live",
        "aria-modal", "aria-multiline", "aria-multiselectable", "aria-orientation",
        "aria-owns", "aria-placeholder", "aria-posinset", "aria-pressed", "aria-readonly",
        "aria-relevant", "aria-required", "aria-roledescription", "aria-rowcount",
        "aria-rowindex", "aria-rowindextext", "aria-rowspan", "aria-selected",
        "aria-setsize", "aria-sort", "aria-valuemax", "aria-valuemin", "aria-valuenow",
        "aria-valuetext",
    }

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        for el in page_data.get("aria_elements", []):
            for attr_name in el.get("aria_attrs", []):
                if attr_name.startswith("aria-") and attr_name not in self.VALID_ARIA_ATTRS:
                    issues.append({
                        "rule_id": self.rule_id,
                        "wcag_criterion": self.wcag_criterion,
                        "wcag_level": self.wcag_level,
                        "severity": "critical",
                        "title": f"Invalid ARIA attribute '{attr_name}'",
                        "description": f"The attribute '{attr_name}' is not a valid WAI-ARIA attribute.",
                        "recommendation": "Use a valid ARIA attribute name. Check for typos in the attribute name.",
                        "element_selector": el.get("selector", ""),
                        "detected_by": "rule",
                    })
        return issues


class AriaValidAttrValueRule(A11yRule):
    """WCAG 4.1.2 - ARIA attribute values must be valid."""

    rule_id = "aria-valid-attr-value"
    wcag_criterion = "4.1.2"
    wcag_level = "A"
    description = "ARIA attribute values must be valid"

    # Attributes with enumerated valid values
    ENUM_ATTRS: dict[str, set[str]] = {
        "aria-autocomplete": {"inline", "list", "both", "none"},
        "aria-checked": {"true", "false", "mixed", "undefined"},
        "aria-current": {"page", "step", "location", "date", "time", "true", "false"},
        "aria-dropeffect": {"copy", "execute", "link", "move", "none", "popup"},
        "aria-expanded": {"true", "false", "undefined"},
        "aria-haspopup": {"true", "false", "menu", "listbox", "tree", "grid", "dialog"},
        "aria-hidden": {"true", "false", "undefined"},
        "aria-invalid": {"true", "false", "grammar", "spelling"},
        "aria-live": {"assertive", "off", "polite"},
        "aria-orientation": {"horizontal", "vertical", "undefined"},
        "aria-pressed": {"true", "false", "mixed", "undefined"},
        "aria-relevant": {"additions", "all", "removals", "text", "additions text"},
        "aria-selected": {"true", "false", "undefined"},
        "aria-sort": {"ascending", "descending", "none", "other"},
    }

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        for el in page_data.get("aria_elements", []):
            attr_values = el.get("aria_attr_values", {})
            for attr_name, value in attr_values.items():
                if attr_name in self.ENUM_ATTRS:
                    valid_values = self.ENUM_ATTRS[attr_name]
                    val_lower = str(value).strip().lower()
                    if val_lower not in valid_values:
                        issues.append({
                            "rule_id": self.rule_id,
                            "wcag_criterion": self.wcag_criterion,
                            "wcag_level": self.wcag_level,
                            "severity": "critical",
                            "title": f"Invalid value for '{attr_name}'",
                            "description": (
                                f"The value '{value}' for '{attr_name}' is not valid. "
                                f"Expected one of: {', '.join(sorted(valid_values))}."
                            ),
                            "recommendation": f"Set '{attr_name}' to one of the valid values: {', '.join(sorted(valid_values))}.",
                            "element_selector": el.get("selector", ""),
                            "detected_by": "rule",
                        })
        return issues


class BypassRule(A11yRule):
    """WCAG 2.4.1 - Bypass Blocks: Page must provide a mechanism to skip navigation."""

    rule_id = "bypass"
    wcag_criterion = "2.4.1"
    wcag_level = "A"
    description = "Pages must provide a mechanism to skip repeated blocks of content"

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        html = page_data.get("html", "")
        if not html:
            return issues

        html_lower = html.lower()
        has_skip_link = bool(re.search(r'<a\b[^>]*href\s*=\s*["\']#', html_lower))
        has_main_landmark = bool(
            re.search(r'<main\b', html_lower)
            or re.search(r'role\s*=\s*["\']main["\']', html_lower)
        )
        has_nav_landmark = bool(
            re.search(r'<nav\b', html_lower)
            or re.search(r'role\s*=\s*["\']navigation["\']', html_lower)
        )

        if not has_skip_link and not has_main_landmark:
            issues.append({
                "rule_id": self.rule_id,
                "wcag_criterion": self.wcag_criterion,
                "wcag_level": self.wcag_level,
                "severity": "major",
                "title": "Page has no skip navigation mechanism",
                "description": (
                    "No skip link or <main> landmark was found. Users who rely on "
                    "keyboard navigation need a way to bypass repeated content blocks."
                ),
                "recommendation": (
                    "Add a skip link (e.g., <a href=\"#main\">Skip to main content</a>) "
                    "or use a <main> landmark to allow assistive technology to jump to content."
                ),
                "detected_by": "rule",
            })
        return issues


class DuplicateIdAriaRule(A11yRule):
    """WCAG 4.1.1 - IDs used in ARIA and label attributes must be unique."""

    rule_id = "duplicate-id-aria"
    wcag_criterion = "4.1.1"
    wcag_level = "A"
    description = "IDs referenced by ARIA attributes and labels must be unique"

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        for dup in page_data.get("duplicate_ids", []):
            is_aria_referenced = dup.get("aria_referenced", False)
            if is_aria_referenced:
                issues.append({
                    "rule_id": self.rule_id,
                    "wcag_criterion": self.wcag_criterion,
                    "wcag_level": self.wcag_level,
                    "severity": "critical",
                    "title": "Duplicate ID used in ARIA/label reference",
                    "description": (
                        f"ID '{dup.get('id')}' appears {dup.get('count')} times and "
                        "is referenced by an ARIA attribute or <label>. "
                        "This can cause assistive technology to reference the wrong element."
                    ),
                    "recommendation": "Ensure each id used by aria-labelledby, aria-describedby, or <label for> is unique.",
                    "element_selector": f"[id='{dup.get('id', '')}']",
                    "detected_by": "rule",
                })
        return issues


class FrameTitleRule(A11yRule):
    """WCAG 4.1.2 - <iframe>/<frame> must have an accessible name (title)."""

    rule_id = "frame-title"
    wcag_criterion = "4.1.2"
    wcag_level = "A"
    description = "<iframe> and <frame> elements must have an accessible name"

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        for frame in page_data.get("frames", []):
            title = (frame.get("title") or "").strip()
            aria_label = (frame.get("aria_label") or "").strip()
            aria_labelledby = (frame.get("aria_labelledby") or "").strip()
            if not title and not aria_label and not aria_labelledby:
                src = frame.get("src", "")[:80]
                issues.append({
                    "rule_id": self.rule_id,
                    "wcag_criterion": self.wcag_criterion,
                    "wcag_level": self.wcag_level,
                    "severity": "major",
                    "title": "Frame missing accessible name",
                    "description": (
                        f"<{frame.get('tag', 'iframe')}> (src='{src}') has no title, "
                        "aria-label, or aria-labelledby attribute."
                    ),
                    "recommendation": "Add a descriptive title attribute to the <iframe>/<frame> element.",
                    "element_selector": f"iframe[src*='{src[:50]}']" if src else "iframe",
                    "detected_by": "rule",
                })
        return issues


class InputImageAltRule(A11yRule):
    """WCAG 1.1.1 - <input type='image'> must have alternative text."""

    rule_id = "input-image-alt"
    wcag_criterion = "1.1.1"
    wcag_level = "A"
    description = "<input type='image'> must have alternative text"

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        for form in page_data.get("forms", []):
            for inp in form.get("inputs", []):
                if inp.get("type") != "image":
                    continue
                alt = (inp.get("alt") or "").strip()
                aria_label = (inp.get("aria_label") or "").strip()
                if not alt and not aria_label:
                    issues.append({
                        "rule_id": self.rule_id,
                        "wcag_criterion": self.wcag_criterion,
                        "wcag_level": self.wcag_level,
                        "severity": "critical",
                        "title": "Image input missing alt text",
                        "description": (
                            f"<input type='image'> (name='{inp.get('name', '')}') "
                            "has no alt or aria-label attribute."
                        ),
                        "recommendation": "Add an alt attribute that describes the button's action.",
                        "element_selector": f"input[type='image'][name='{inp.get('name', '')}']",
                        "detected_by": "rule",
                    })
        # Also check via HTML fallback
        html = page_data.get("html", "")
        if html:
            for m in re.finditer(r'<input\b([^>]*type\s*=\s*["\']image["\'][^>]*)>', html, re.IGNORECASE):
                attrs = m.group(1)
                has_alt = re.search(r'\balt\s*=\s*["\'][^"\']+["\']', attrs, re.IGNORECASE)
                has_aria = re.search(r'\baria-label\s*=\s*["\'][^"\']+["\']', attrs, re.IGNORECASE)
                if not has_alt and not has_aria:
                    # Only add if not already caught by form data above
                    name_m = re.search(r'\bname\s*=\s*["\']([^"\']*)["\']', attrs)
                    name = name_m.group(1) if name_m else ""
                    already_found = any(
                        i["element_selector"] == f"input[type='image'][name='{name}']"
                        for i in issues
                    )
                    if not already_found:
                        issues.append({
                            "rule_id": self.rule_id,
                            "wcag_criterion": self.wcag_criterion,
                            "wcag_level": self.wcag_level,
                            "severity": "critical",
                            "title": "Image input missing alt text",
                            "description": f"<input type='image'> has no alt or aria-label attribute.",
                            "recommendation": "Add an alt attribute that describes the button's action.",
                            "element_selector": f"input[type='image'][name='{name}']" if name else "input[type='image']",
                            "detected_by": "rule",
                        })
        return issues


class MetaRefreshRule(A11yRule):
    """WCAG 2.2.1 - <meta http-equiv='refresh'> must not be used for delayed redirect."""

    rule_id = "meta-refresh"
    wcag_criterion = "2.2.1"
    wcag_level = "A"
    description = "Pages must not use <meta http-equiv='refresh'> for delayed redirect"

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        html = page_data.get("html", "")
        if not html:
            return issues

        pattern = r'<meta\b[^>]*http-equiv\s*=\s*["\']refresh["\'][^>]*content\s*=\s*["\']([^"\']*)["\']'
        for m in re.finditer(pattern, html, re.IGNORECASE):
            content = m.group(1).strip()
            # content like "5; url=..." or just "5"
            delay_match = re.match(r"(\d+)", content)
            if delay_match:
                delay = int(delay_match.group(1))
                if delay > 0:
                    issues.append({
                        "rule_id": self.rule_id,
                        "wcag_criterion": self.wcag_criterion,
                        "wcag_level": self.wcag_level,
                        "severity": "critical",
                        "title": "Page uses meta refresh to redirect",
                        "description": (
                            f"<meta http-equiv='refresh'> with delay of {delay} seconds found. "
                            "Timed refreshes can disorient users."
                        ),
                        "recommendation": "Remove the meta refresh. Use server-side redirects (HTTP 301/302) instead.",
                        "element_selector": "meta[http-equiv='refresh']",
                        "detected_by": "rule",
                    })
        return issues


class NestedInteractiveRule(A11yRule):
    """WCAG 4.1.2 - Interactive controls must not be nested inside each other."""

    rule_id = "nested-interactive"
    wcag_criterion = "4.1.2"
    wcag_level = "A"
    description = "Interactive controls must not be nested inside other interactive controls"

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        for el in page_data.get("nested_interactive", []):
            issues.append({
                "rule_id": self.rule_id,
                "wcag_criterion": self.wcag_criterion,
                "wcag_level": self.wcag_level,
                "severity": "major",
                "title": "Nested interactive elements",
                "description": (
                    f"Interactive element <{el.get('child_tag', '')}>'{el.get('child_text', '')[:30]}' "
                    f"is nested inside <{el.get('parent_tag', '')}>'{el.get('parent_text', '')[:30]}'."
                ),
                "recommendation": (
                    "Do not nest interactive elements (buttons, links, inputs). "
                    "Restructure the markup so each interactive control is independent."
                ),
                "element_selector": el.get("selector", ""),
                "detected_by": "rule",
            })
        return issues


class ScrollableRegionFocusableRule(A11yRule):
    """WCAG 2.1.1 - Scrollable regions must be keyboard accessible."""

    rule_id = "scrollable-region-focusable"
    wcag_criterion = "2.1.1"
    wcag_level = "A"
    description = "Scrollable regions must be accessible via keyboard"

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        for el in page_data.get("scrollable_regions", []):
            if not el.get("is_focusable", False) and not el.get("has_focusable_child", False):
                issues.append({
                    "rule_id": self.rule_id,
                    "wcag_criterion": self.wcag_criterion,
                    "wcag_level": self.wcag_level,
                    "severity": "major",
                    "title": "Scrollable region not keyboard accessible",
                    "description": (
                        f"A scrollable <{el.get('tag', 'div')}> element is not focusable "
                        "and does not contain focusable content. Keyboard users cannot scroll it."
                    ),
                    "recommendation": (
                        "Add tabindex='0' and an appropriate role (e.g., role='region') "
                        "with an aria-label to make the scrollable area keyboard accessible."
                    ),
                    "element_selector": el.get("selector", ""),
                    "detected_by": "rule",
                })
        return issues


class SelectNameRule(A11yRule):
    """WCAG 4.1.2 - <select> elements must have an accessible name."""

    rule_id = "select-name"
    wcag_criterion = "4.1.2"
    wcag_level = "A"
    description = "<select> elements must have an accessible name"

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        for form in page_data.get("forms", []):
            for inp in form.get("inputs", []):
                tag = inp.get("tag", "").lower()
                if tag != "select":
                    continue
                has_label = inp.get("has_label", False)
                has_aria = bool(inp.get("aria_label"))
                has_aria_labelledby = bool(inp.get("aria_labelledby"))
                has_title = bool(inp.get("title"))
                if not has_label and not has_aria and not has_aria_labelledby and not has_title:
                    issues.append({
                        "rule_id": self.rule_id,
                        "wcag_criterion": self.wcag_criterion,
                        "wcag_level": self.wcag_level,
                        "severity": "critical",
                        "title": "<select> missing accessible name",
                        "description": (
                            f"<select> element (name='{inp.get('name', '')}') "
                            "has no associated <label>, aria-label, aria-labelledby, or title."
                        ),
                        "recommendation": (
                            "Add a <label> with a 'for' attribute matching the select's id, "
                            "or add aria-label / aria-labelledby."
                        ),
                        "element_selector": f"select[name='{inp.get('name', '')}']",
                        "detected_by": "rule",
                    })
        return issues


class SvgImgAltRule(A11yRule):
    """WCAG 1.1.1 - <svg> with role='img' must have alternative text."""

    rule_id = "svg-img-alt"
    wcag_criterion = "1.1.1"
    wcag_level = "A"
    description = "<svg> elements with role='img' must have alternative text"

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        for el in page_data.get("svg_images", []):
            role = (el.get("role") or "").lower()
            if role != "img":
                continue
            aria_label = (el.get("aria_label") or "").strip()
            aria_labelledby = (el.get("aria_labelledby") or "").strip()
            has_title = el.get("has_title_child", False)
            if not aria_label and not aria_labelledby and not has_title:
                issues.append({
                    "rule_id": self.rule_id,
                    "wcag_criterion": self.wcag_criterion,
                    "wcag_level": self.wcag_level,
                    "severity": "major",
                    "title": "SVG image missing alternative text",
                    "description": (
                        "An <svg> element with role='img' has no aria-label, "
                        "aria-labelledby, or <title> child element."
                    ),
                    "recommendation": (
                        "Add aria-label, aria-labelledby, or a <title> child element "
                        "to provide alternative text for the SVG image."
                    ),
                    "element_selector": el.get("selector", "svg[role='img']"),
                    "detected_by": "rule",
                })
        return issues


class TdHeadersAttrRule(A11yRule):
    """WCAG 1.3.1 - Table <td> headers attribute must reference valid <th> ids."""

    rule_id = "td-headers-attr"
    wcag_criterion = "1.3.1"
    wcag_level = "A"
    description = "Table data cells using the headers attribute must reference valid header IDs"

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        for table in page_data.get("tables", []):
            th_ids = set(table.get("th_ids", []))
            for cell in table.get("cells_with_headers", []):
                header_refs = cell.get("headers", "").split()
                for ref in header_refs:
                    if ref and ref not in th_ids:
                        issues.append({
                            "rule_id": self.rule_id,
                            "wcag_criterion": self.wcag_criterion,
                            "wcag_level": self.wcag_level,
                            "severity": "major",
                            "title": "Invalid headers reference in table cell",
                            "description": (
                                f"Table cell references header id='{ref}' "
                                "which does not exist in the table."
                            ),
                            "recommendation": "Ensure the headers attribute references valid <th> id values in the same table.",
                            "element_selector": cell.get("selector", "td[headers]"),
                            "detected_by": "rule",
                        })
        return issues


class ThHasDataCellsRule(A11yRule):
    """WCAG 1.3.1 - Table <th> elements must be associated with data cells."""

    rule_id = "th-has-data-cells"
    wcag_criterion = "1.3.1"
    wcag_level = "A"
    description = "Table header cells must be associated with data cells"

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        for table in page_data.get("tables", []):
            for th in table.get("orphan_headers", []):
                issues.append({
                    "rule_id": self.rule_id,
                    "wcag_criterion": self.wcag_criterion,
                    "wcag_level": self.wcag_level,
                    "severity": "major",
                    "title": "Table header not associated with data cells",
                    "description": (
                        f"<th> element '{th.get('text', '')[:40]}' is not associated with any data cells."
                    ),
                    "recommendation": (
                        "Ensure <th> elements are in the correct position (row/column headers) "
                        "or use the scope attribute to clarify associations."
                    ),
                    "element_selector": th.get("selector", "th"),
                    "detected_by": "rule",
                })
        return issues


class VideoCaptionRule(A11yRule):
    """WCAG 1.2.2 - <video> elements must have captions."""

    rule_id = "video-caption"
    wcag_criterion = "1.2.2"
    wcag_level = "A"
    description = "<video> elements must provide captions"

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        html = page_data.get("html", "")
        if not html:
            return issues

        for m in re.finditer(r"<video\b[^>]*>(.*?)</video>", html, re.IGNORECASE | re.DOTALL):
            video_content = m.group(1)
            has_track = bool(re.search(
                r'<track\b[^>]*kind\s*=\s*["\'](?:captions|subtitles)["\']',
                video_content, re.IGNORECASE
            ))
            if not has_track:
                src_match = re.search(r'\bsrc\s*=\s*["\']([^"\']*)["\']', m.group(0), re.IGNORECASE)
                src = src_match.group(1)[:80] if src_match else ""
                issues.append({
                    "rule_id": self.rule_id,
                    "wcag_criterion": self.wcag_criterion,
                    "wcag_level": self.wcag_level,
                    "severity": "critical",
                    "title": "Video missing captions",
                    "description": (
                        f"A <video> element{' (src=' + src + ')' if src else ''} "
                        "does not have a <track kind='captions'> or <track kind='subtitles'>."
                    ),
                    "recommendation": (
                        "Add a <track kind='captions' src='captions.vtt' srclang='...'> "
                        "element inside the <video> to provide captions."
                    ),
                    "element_selector": f"video[src*='{src[:50]}']" if src else "video",
                    "detected_by": "rule",
                })
        return issues


class AutocompleteValidRule(A11yRule):
    """WCAG 1.3.5 - autocomplete attribute values must be correct and appropriate."""

    rule_id = "autocomplete-valid"
    wcag_criterion = "1.3.5"
    wcag_level = "AA"
    description = "autocomplete attribute values must be correct and appropriate for the form field"

    VALID_AUTOCOMPLETE_VALUES = {
        "off", "on", "name", "honorific-prefix", "given-name", "additional-name",
        "family-name", "honorific-suffix", "nickname", "email", "username",
        "new-password", "current-password", "one-time-code", "organization-title",
        "organization", "street-address", "address-line1", "address-line2",
        "address-line3", "address-level4", "address-level3", "address-level2",
        "address-level1", "country", "country-name", "postal-code", "cc-name",
        "cc-given-name", "cc-additional-name", "cc-family-name", "cc-number",
        "cc-exp", "cc-exp-month", "cc-exp-year", "cc-csc", "cc-type",
        "transaction-currency", "transaction-amount", "language", "bday",
        "bday-day", "bday-month", "bday-year", "sex", "tel", "tel-country-code",
        "tel-national", "tel-area-code", "tel-local", "tel-extension", "impp",
        "url", "photo",
    }

    # Section prefixes allowed before the autocomplete token
    SECTION_PREFIX_RE = re.compile(r"^section-\S+$")
    BILLING_SHIPPING = {"shipping", "billing"}

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        for inp in page_data.get("autocomplete_inputs", []):
            raw = (inp.get("autocomplete") or "").strip()
            if not raw or raw == "off" or raw == "on":
                continue

            tokens = raw.lower().split()
            # Strip section- prefix and billing/shipping
            filtered = [
                t for t in tokens
                if t not in self.BILLING_SHIPPING and not self.SECTION_PREFIX_RE.match(t)
            ]
            for token in filtered:
                if token not in self.VALID_AUTOCOMPLETE_VALUES:
                    issues.append({
                        "rule_id": self.rule_id,
                        "wcag_criterion": self.wcag_criterion,
                        "wcag_level": self.wcag_level,
                        "severity": "major",
                        "title": f"Invalid autocomplete value '{token}'",
                        "description": (
                            f"Input '{inp.get('name', inp.get('id', 'unknown'))}' has "
                            f"autocomplete value '{token}' which is not a valid autocomplete token."
                        ),
                        "recommendation": "Use a valid HTML autocomplete token (e.g., 'name', 'email', 'tel').",
                        "element_selector": f"input[name='{inp.get('name', '')}']",
                        "detected_by": "rule",
                    })
        return issues


class AvoidInlineSpacingRule(A11yRule):
    """WCAG 1.4.12 - Inline style text spacing must allow user customization."""

    rule_id = "avoid-inline-spacing"
    wcag_criterion = "1.4.12"
    wcag_level = "AA"
    description = "Inline style text spacing properties must allow user override"

    SPACING_PROPS = ["letter-spacing", "word-spacing", "line-height"]

    def check(self, page_data: dict[str, Any]) -> list[dict]:
        issues = []
        for el in page_data.get("inline_style_elements", []):
            style = (el.get("style") or "").lower()
            if not style:
                continue
            for prop in self.SPACING_PROPS:
                if prop in style and "!important" in style:
                    # Check if this specific property has !important
                    pattern = rf"{re.escape(prop)}\s*:[^;]*!important"
                    if re.search(pattern, style):
                        issues.append({
                            "rule_id": self.rule_id,
                            "wcag_criterion": self.wcag_criterion,
                            "wcag_level": self.wcag_level,
                            "severity": "major",
                            "title": f"Inline style locks '{prop}' with !important",
                            "description": (
                                f"Element <{el.get('tag', '')}> has inline style setting "
                                f"'{prop}' with !important, preventing user customization."
                            ),
                            "recommendation": (
                                f"Remove !important from the inline '{prop}' style, "
                                "or move the style to a stylesheet where users can override it."
                            ),
                            "element_selector": el.get("selector", ""),
                            "detected_by": "rule",
                        })
        return issues


# Register all rules
for rule_class in [
    # Level A rules
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
    AreaAltRule,
    AriaAllowedAttrRule,
    AriaHiddenFocusRule,
    AriaRequiredAttrRule,
    AriaRequiredChildrenRule,
    AriaRequiredParentRule,
    AriaRolesRule,
    AriaValidAttrRule,
    AriaValidAttrValueRule,
    BypassRule,
    DuplicateIdAriaRule,
    FrameTitleRule,
    InputImageAltRule,
    MetaRefreshRule,
    NestedInteractiveRule,
    ScrollableRegionFocusableRule,
    SelectNameRule,
    SvgImgAltRule,
    TdHeadersAttrRule,
    ThHasDataCellsRule,
    VideoCaptionRule,
    # Level AA rules
    ResizeTextRule,
    InputPurposeRule,
    LanguageOfPartsRule,
    TextSpacingRule,
    NonTextContrastRule,
    AriaLiveRegionRule,
    MultipleWaysRule,
    ImageLongAltRule,
    AutocompleteValidRule,
    AvoidInlineSpacingRule,
    # Level AAA rules
    LinkTargetBlankRule,
]:
    registry.register(rule_class())
