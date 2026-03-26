from __future__ import annotations

from langchain_core.tools import tool


@tool
def check_color_contrast(foreground: str, background: str) -> dict:
    """Check if two colors meet WCAG contrast ratio requirements.

    Args:
        foreground: Foreground color in hex format (e.g., '#333333')
        background: Background color in hex format (e.g., '#ffffff')

    Returns:
        Dictionary with contrast ratio and pass/fail for AA and AAA levels
    """
    def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def relative_luminance(r: int, g: int, b: int) -> float:
        def linearize(c: int) -> float:
            c_srgb = c / 255
            return c_srgb / 12.92 if c_srgb <= 0.04045 else ((c_srgb + 0.055) / 1.055) ** 2.4
        return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)

    try:
        fg_rgb = hex_to_rgb(foreground)
        bg_rgb = hex_to_rgb(background)

        l1 = relative_luminance(*fg_rgb)
        l2 = relative_luminance(*bg_rgb)

        lighter = max(l1, l2)
        darker = min(l1, l2)
        ratio = (lighter + 0.05) / (darker + 0.05)

        return {
            "contrast_ratio": round(ratio, 2),
            "passes_aa_normal": ratio >= 4.5,
            "passes_aa_large": ratio >= 3.0,
            "passes_aaa_normal": ratio >= 7.0,
            "passes_aaa_large": ratio >= 4.5,
        }
    except (ValueError, IndexError):
        return {"error": "Invalid color format"}


@tool
def validate_aria_attributes(element_html: str) -> dict:
    """Validate ARIA attributes on an HTML element.

    Args:
        element_html: HTML string of the element to validate

    Returns:
        Dictionary with validation results
    """
    import re

    issues = []

    # Check for required ARIA attributes
    role_match = re.search(r'role=["\']([^"\']+)["\']', element_html)
    if role_match:
        role = role_match.group(1)

        # Roles that require aria-label or aria-labelledby
        label_required_roles = [
            "dialog", "alertdialog", "navigation", "region",
            "form", "complementary", "search",
        ]
        if role in label_required_roles:
            has_label = (
                'aria-label=' in element_html
                or 'aria-labelledby=' in element_html
            )
            if not has_label:
                issues.append({
                    "issue": f"Role '{role}' requires aria-label or aria-labelledby",
                    "wcag": "4.1.2",
                })

    # Check for invalid ARIA attribute values
    aria_hidden = re.search(r'aria-hidden=["\']([^"\']+)["\']', element_html)
    if aria_hidden and aria_hidden.group(1) not in ("true", "false"):
        issues.append({
            "issue": f"Invalid aria-hidden value: {aria_hidden.group(1)}",
            "wcag": "4.1.2",
        })

    # Check for tabindex with aria-hidden
    if 'aria-hidden="true"' in element_html and 'tabindex=' in element_html:
        tabindex = re.search(r'tabindex=["\'](-?\d+)["\']', element_html)
        if tabindex and int(tabindex.group(1)) >= 0:
            issues.append({
                "issue": "Element with aria-hidden='true' should not be focusable",
                "wcag": "4.1.2",
            })

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "issues_count": len(issues),
    }


@tool
def check_heading_hierarchy(headings: list[dict]) -> dict:
    """Check if heading elements follow a proper hierarchy.

    Args:
        headings: List of heading info dicts with 'level' and 'text' keys

    Returns:
        Dictionary with hierarchy validation results
    """
    issues = []

    if not headings:
        return {"valid": True, "issues": [], "has_h1": False}

    # Check for h1
    has_h1 = any(h.get("level") == 1 for h in headings)
    if not has_h1:
        issues.append({
            "issue": "Page is missing an h1 heading",
            "wcag": "1.3.1",
        })

    # Check for skipped levels
    prev_level = 0
    for h in headings:
        level = h.get("level", 0)
        if level > prev_level + 1 and prev_level > 0:
            issues.append({
                "issue": f"Heading level skipped from h{prev_level} to h{level}: '{h.get('text', '')[:50]}'",
                "wcag": "1.3.1",
            })
        prev_level = level

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "has_h1": has_h1,
        "heading_count": len(headings),
    }
