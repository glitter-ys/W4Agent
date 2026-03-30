from __future__ import annotations

import os
import re
from typing import Any

from PIL import Image, ImageDraw, ImageFont
import structlog

logger = structlog.get_logger()

# Severity color scheme: (border_color, label_bg_color)
SEVERITY_COLORS = {
    "critical": ((220, 38, 38), (220, 38, 38)),     # Red
    "major": ((234, 140, 22), (234, 140, 22)),       # Orange
    "minor": ((202, 168, 24), (202, 168, 24)),       # Gold
    "info": ((22, 119, 255), (22, 119, 255)),        # Blue
}

DEFAULT_COLOR = ((128, 128, 128), (128, 128, 128))

BORDER_WIDTH = 3
LABEL_PADDING = 4
LEGEND_LINE_HEIGHT = 20
LEGEND_MARGIN = 16

# Font search paths, ordered by priority.
# CJK-capable fonts first so Chinese/Japanese/Korean text renders correctly.
_CJK_FONT_PATHS = [
    # Linux (Debian/Ubuntu) — installed via fonts-noto-cjk
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    # macOS
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    # Fallback non-CJK
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]

_CJK_FONT_BOLD_PATHS = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJKsc-Bold.otf",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a font that supports CJK characters, with fallbacks."""
    paths = _CJK_FONT_BOLD_PATHS if bold else _CJK_FONT_PATHS
    for path in paths:
        if os.path.isfile(path):
            try:
                return ImageFont.truetype(path, size)
            except (OSError, IOError):
                continue
    return ImageFont.load_default()


def _extract_tag_from_selector(selector: str) -> str | None:
    """Extract the leading tag name from a CSS selector string."""
    m = re.match(r"^([a-zA-Z][a-zA-Z0-9]*)", selector)
    return m.group(1).lower() if m else None


def _extract_tag_from_html(html: str) -> str | None:
    """Extract the tag name from an HTML snippet like '<img src=...>'."""
    m = re.match(r"<([a-zA-Z][a-zA-Z0-9]*)", html.strip())
    return m.group(1).lower() if m else None


def _extract_attr_from_html(html: str, attr: str) -> str | None:
    """Extract an attribute value from an HTML snippet."""
    pattern = rf"""{attr}\s*=\s*(?:"([^"]*)"|'([^']*)')"""
    m = re.search(pattern, html, re.IGNORECASE)
    if m:
        return m.group(1) if m.group(1) is not None else m.group(2)
    return None


def _normalize(text: str | None) -> str:
    """Lowercase, strip, and collapse whitespace for fuzzy comparison."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.strip().lower())


def _match_issues_to_bboxes(
    issues: list[dict[str, Any]],
    bounding_boxes: list[dict[str, Any]],
) -> list[tuple[int, dict, dict]]:
    """Match issues to bounding boxes using multiple strategies.

    Strategies (in priority order):
    1. Exact selector match
    2. element_html content matching (tag + attributes)
    3. Tag + text/alt fuzzy match
    4. Positional fallback for remaining unmatched issues

    Returns list of (1-based index, issue, bbox_rect) tuples.
    """
    # Build lookup structures
    bbox_by_selector: dict[str, int] = {}
    for i, bb in enumerate(bounding_boxes):
        selector = bb.get("selector")
        if selector and bb.get("bbox"):
            bbox_by_selector[selector] = i

    used_bbox_indices: set[int] = set()
    matched: list[tuple[int, dict, dict]] = []
    unmatched_issues: list[tuple[int, dict]] = []  # (original issue index, issue)
    idx = 0

    for issue_idx, issue in enumerate(issues):
        selector = issue.get("element_selector")
        bbox_rect = None

        # Strategy 1: Exact selector match
        if selector and selector in bbox_by_selector:
            bi = bbox_by_selector[selector]
            if bi not in used_bbox_indices:
                bbox_rect = bounding_boxes[bi]["bbox"]
                used_bbox_indices.add(bi)

        # Strategy 2: element_html content matching
        if bbox_rect is None:
            element_html = issue.get("element_html") or ""
            if element_html:
                html_tag = _extract_tag_from_html(element_html)
                html_alt = _normalize(_extract_attr_from_html(element_html, "alt"))
                html_src = _extract_attr_from_html(element_html, "src")
                html_aria = _normalize(
                    _extract_attr_from_html(element_html, "aria-label")
                )

                best_score = 0
                best_bi = -1
                for bi, bb in enumerate(bounding_boxes):
                    if bi in used_bbox_indices or not bb.get("bbox"):
                        continue
                    score = 0
                    # Tag must match if both present
                    bb_tag = bb.get("tag", "").lower()
                    if html_tag and bb_tag and html_tag != bb_tag:
                        continue
                    if html_tag and bb_tag and html_tag == bb_tag:
                        score += 1

                    # Alt text match
                    bb_alt = _normalize(bb.get("alt"))
                    if html_alt and bb_alt and html_alt == bb_alt:
                        score += 3

                    # Aria-label match
                    bb_aria = _normalize(bb.get("aria_label"))
                    if html_aria and bb_aria and html_aria == bb_aria:
                        score += 3

                    # Text content overlap
                    bb_text = _normalize(bb.get("text"))
                    # Extract inner text from element_html (strip tags)
                    inner_text = _normalize(re.sub(r"<[^>]+>", "", element_html))
                    if inner_text and bb_text and (
                        inner_text in bb_text or bb_text in inner_text
                    ):
                        score += 2

                    # src substring match (for images)
                    if html_src and bb.get("selector"):
                        # Check if the src filename appears in the selector
                        src_basename = html_src.rsplit("/", 1)[-1].split("?")[0]
                        if src_basename and src_basename in (bb.get("selector") or ""):
                            score += 2

                    if score > best_score:
                        best_score = score
                        best_bi = bi

                if best_score >= 2 and best_bi >= 0:
                    bbox_rect = bounding_boxes[best_bi]["bbox"]
                    used_bbox_indices.add(best_bi)

        # Strategy 3: Tag + text/alt fuzzy match from selector
        if bbox_rect is None and selector:
            sel_tag = _extract_tag_from_selector(selector)
            if sel_tag:
                best_score = 0
                best_bi = -1
                for bi, bb in enumerate(bounding_boxes):
                    if bi in used_bbox_indices or not bb.get("bbox"):
                        continue
                    bb_tag = bb.get("tag", "").lower()
                    if bb_tag != sel_tag:
                        continue
                    score = 1  # tag matches

                    # Try to extract identifiers from the selector for matching
                    # e.g. img[alt='Logo'] -> match on alt='Logo'
                    alt_m = re.search(
                        r"""\[alt\s*[\*~\|^$]?=\s*['"]([^'"]+)['"]\]""",
                        selector,
                        re.IGNORECASE,
                    )
                    if alt_m:
                        expected_alt = _normalize(alt_m.group(1))
                        bb_alt = _normalize(bb.get("alt"))
                        if expected_alt and bb_alt and (
                            expected_alt in bb_alt or bb_alt in expected_alt
                        ):
                            score += 3

                    # Match src attribute from selector
                    src_m = re.search(
                        r"""\[src\s*[\*~\|^$]?=\s*['"]([^'"]+)['"]\]""",
                        selector,
                        re.IGNORECASE,
                    )
                    if src_m:
                        expected_src = src_m.group(1)
                        bb_text_all = f"{bb.get('selector', '')} {bb.get('alt', '')} {bb.get('text', '')}"
                        if expected_src in bb_text_all:
                            score += 2

                    # ID match from selector (#some-id)
                    id_m = re.search(r"#([\w-]+)", selector)
                    if id_m:
                        expected_id = id_m.group(1)
                        bb_selector = bb.get("selector", "")
                        if f"#{expected_id}" in bb_selector:
                            score += 3

                    if score > best_score:
                        best_score = score
                        best_bi = bi

                if best_score >= 2 and best_bi >= 0:
                    bbox_rect = bounding_boxes[best_bi]["bbox"]
                    used_bbox_indices.add(best_bi)

        if bbox_rect is not None:
            idx += 1
            matched.append((idx, issue, bbox_rect))
        else:
            unmatched_issues.append((issue_idx, issue))

    # Strategy 4: Positional fallback — assign remaining bboxes by y,x order
    if unmatched_issues:
        remaining_bboxes = [
            (i, bb)
            for i, bb in enumerate(bounding_boxes)
            if i not in used_bbox_indices and bb.get("bbox")
        ]
        # Sort remaining bboxes by position (top-to-bottom, left-to-right)
        remaining_bboxes.sort(
            key=lambda item: (item[1]["bbox"]["y"], item[1]["bbox"]["x"])
        )

        for (_, issue), (bi, bb) in zip(unmatched_issues, remaining_bboxes):
            idx += 1
            matched.append((idx, issue, bb["bbox"]))
            used_bbox_indices.add(bi)

    return matched


class VisualAnnotator:
    """Renders colored bounding box annotations on page screenshots."""

    def annotate_screenshot(
        self,
        screenshot_path: str,
        issues: list[dict[str, Any]],
        bounding_boxes: list[dict[str, Any]],
    ) -> str | None:
        """Draw issue annotations on a screenshot and save the result.

        Args:
            screenshot_path: Path to the original screenshot PNG.
            issues: List of issue dicts (must have element_selector, severity, title).
            bounding_boxes: List of bbox dicts from PageAnalyzer (must have selector, bbox).

        Returns:
            Path to the annotated screenshot, or None on failure.
        """
        if not screenshot_path or not os.path.isfile(screenshot_path):
            logger.warning("annotate_missing_screenshot", path=screenshot_path)
            return None

        if not issues:
            return None

        # Match issues to bounding boxes using multi-strategy matching
        matched = _match_issues_to_bboxes(issues, bounding_boxes)

        if not matched:
            logger.info("annotate_no_matched_issues", path=screenshot_path)
            return None

        try:
            img = Image.open(screenshot_path).convert("RGBA")
        except Exception as e:
            logger.error("annotate_open_error", path=screenshot_path, error=str(e))
            return None

        # Create overlay for semi-transparent drawing
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw_overlay = ImageDraw.Draw(overlay)
        draw_main = ImageDraw.Draw(img)

        # Load CJK-capable fonts
        font = _load_font(13, bold=True)
        small_font = _load_font(11, bold=False)

        # Draw bounding boxes and labels
        for num, issue, bbox in matched:
            severity = issue.get("severity", "info")
            border_color, label_bg = SEVERITY_COLORS.get(severity, DEFAULT_COLOR)
            title = issue.get("title", "Issue")

            x, y, w, h = bbox["x"], bbox["y"], bbox["width"], bbox["height"]

            # Draw semi-transparent filled rectangle
            fill_color = (*border_color, 40)
            draw_overlay.rectangle([x, y, x + w, y + h], fill=fill_color)

            # Draw border
            for i in range(BORDER_WIDTH):
                draw_main.rectangle(
                    [x - i, y - i, x + w + i, y + h + i],
                    outline=(*border_color, 255),
                )

            # Draw number label at top-left
            label_text = f" {num} "
            text_bbox = draw_main.textbbox((0, 0), label_text, font=font)
            label_w = text_bbox[2] - text_bbox[0] + LABEL_PADDING * 2
            label_h = text_bbox[3] - text_bbox[1] + LABEL_PADDING * 2

            label_x = x
            label_y = max(0, y - label_h)
            draw_main.rectangle(
                [label_x, label_y, label_x + label_w, label_y + label_h],
                fill=(*label_bg, 230),
            )
            draw_main.text(
                (label_x + LABEL_PADDING, label_y + LABEL_PADDING),
                label_text,
                fill=(255, 255, 255),
                font=font,
            )

        # Composite overlay onto main image
        img = Image.alpha_composite(img, overlay)
        img = img.convert("RGB")

        # Draw legend at the bottom
        legend_height = LEGEND_MARGIN * 2 + len(matched) * LEGEND_LINE_HEIGHT + LEGEND_LINE_HEIGHT
        legend_img = Image.new("RGB", (img.width, legend_height), (255, 255, 255))
        legend_draw = ImageDraw.Draw(legend_img)

        # Legend title
        legend_draw.text(
            (LEGEND_MARGIN, LEGEND_MARGIN // 2),
            "问题图例:",
            fill=(0, 0, 0),
            font=font,
        )

        y_offset = LEGEND_MARGIN // 2 + LEGEND_LINE_HEIGHT
        for num, issue, _bbox in matched:
            severity = issue.get("severity", "info")
            border_color, _ = SEVERITY_COLORS.get(severity, DEFAULT_COLOR)
            title = issue.get("title", "Issue")
            severity_label = severity.upper()

            # Color swatch
            legend_draw.rectangle(
                [LEGEND_MARGIN, y_offset + 2, LEGEND_MARGIN + 14, y_offset + 16],
                fill=border_color,
            )
            # Text
            legend_draw.text(
                (LEGEND_MARGIN + 20, y_offset),
                f"#{num} [{severity_label}] {title[:80]}",
                fill=(50, 50, 50),
                font=small_font,
            )
            y_offset += LEGEND_LINE_HEIGHT

        # Combine main image and legend
        combined = Image.new("RGB", (img.width, img.height + legend_height), (255, 255, 255))
        combined.paste(img, (0, 0))
        combined.paste(legend_img, (0, img.height))

        # Save annotated screenshot
        directory = os.path.dirname(screenshot_path)
        basename = os.path.basename(screenshot_path)
        annotated_path = os.path.join(directory, f"annotated_{basename}")

        try:
            combined.save(annotated_path, "PNG")
            logger.info("annotated_screenshot_saved", path=annotated_path, issues=len(matched))
            return annotated_path
        except Exception as e:
            logger.error("annotate_save_error", path=annotated_path, error=str(e))
            return None
