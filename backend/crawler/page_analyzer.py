from __future__ import annotations

import hashlib
import json
from typing import Any

from playwright.async_api import Page
import structlog

logger = structlog.get_logger()


class PageAnalyzer:
    """Analyzes web pages to extract accessibility-relevant information.

    Combines DOM analysis, accessibility tree parsing, and content hashing
    for deduplication.
    """

    async def analyze(self, page: Page) -> dict[str, Any]:
        """Perform comprehensive page analysis.

        Returns a dictionary containing:
        - url, title: Basic page info
        - a11y_tree: Accessibility tree snapshot
        - headings: Heading hierarchy
        - images: Image elements with alt attributes
        - forms: Form elements and their labels
        - links: All links on the page
        - interactive_elements: Buttons, inputs, etc.
        - landmarks: ARIA landmarks
        - content_hash: Hash for deduplication
        - html: Trimmed HTML of the page
        - bounding_boxes: Element bounding boxes for visual annotation
        """
        url = page.url
        title = await page.title()

        # Gather page data in parallel
        a11y_tree = await self._get_a11y_tree(page)
        page_data = await self._extract_page_data(page)
        content_hash = await self._compute_content_hash(page)
        bounding_boxes = await self._extract_element_bounding_boxes(page)

        return {
            "url": url,
            "title": title,
            "a11y_tree": a11y_tree,
            "headings": page_data.get("headings", []),
            "images": page_data.get("images", []),
            "forms": page_data.get("forms", []),
            "links": page_data.get("links", []),
            "interactive_elements": page_data.get("interactive_elements", []),
            "landmarks": page_data.get("landmarks", []),
            "content_hash": content_hash,
            "html": page_data.get("html", ""),
            "lang": page_data.get("lang", ""),
            "bounding_boxes": bounding_boxes,
            # AA-relevant data
            "viewport_meta": page_data.get("viewport_meta", ""),
            "tabindex_elements": page_data.get("tabindex_elements", []),
            "autocomplete_inputs": page_data.get("autocomplete_inputs", []),
            "text_samples": page_data.get("text_samples", []),
            "focus_styles": page_data.get("focus_styles", []),
            "lang_parts": page_data.get("lang_parts", []),
            "aria_live_regions": page_data.get("aria_live_regions", []),
            "duplicate_ids": page_data.get("duplicate_ids", []),
        }

    async def _get_a11y_tree(self, page: Page) -> dict | None:
        """Get the accessibility tree snapshot."""
        try:
            return await page.accessibility.snapshot()
        except Exception as e:
            logger.warning("a11y_tree_error", error=str(e))
            return None

    async def _extract_page_data(self, page: Page) -> dict:
        """Extract structured data from the page DOM."""
        try:
            data = await page.evaluate("""() => {
                // Headings
                const headings = Array.from(document.querySelectorAll('h1,h2,h3,h4,h5,h6'))
                    .map(h => ({
                        level: parseInt(h.tagName[1]),
                        text: h.textContent.trim().slice(0, 200),
                        id: h.id || null,
                    }));

                // Images
                const images = Array.from(document.querySelectorAll('img'))
                    .map(img => ({
                        src: img.src,
                        alt: img.alt,
                        has_alt: img.hasAttribute('alt'),
                        width: img.naturalWidth,
                        height: img.naturalHeight,
                        role: img.getAttribute('role'),
                    }));

                // Forms
                const forms = Array.from(document.querySelectorAll('form')).map(form => {
                    const inputs = Array.from(form.querySelectorAll('input,select,textarea'))
                        .map(input => ({
                            tag: input.tagName.toLowerCase(),
                            type: input.type,
                            name: input.name,
                            id: input.id,
                            has_label: !!document.querySelector(`label[for="${input.id}"]`),
                            aria_label: input.getAttribute('aria-label'),
                            placeholder: input.placeholder,
                            required: input.required,
                        }));
                    return {
                        action: form.action,
                        method: form.method,
                        inputs: inputs,
                    };
                });

                // Links
                const links = Array.from(document.querySelectorAll('a[href]'))
                    .slice(0, 200)
                    .map(a => ({
                        href: a.href,
                        text: a.textContent.trim().slice(0, 100),
                        target: a.target,
                        aria_label: a.getAttribute('aria-label'),
                    }));

                // Interactive elements
                const interactive = Array.from(document.querySelectorAll(
                    'button, [role="button"], input[type="submit"], input[type="button"]'
                )).map(el => ({
                    tag: el.tagName.toLowerCase(),
                    text: el.textContent.trim().slice(0, 100),
                    type: el.type || null,
                    aria_label: el.getAttribute('aria-label'),
                    disabled: el.disabled,
                }));

                // ARIA landmarks
                const landmarks = Array.from(document.querySelectorAll(
                    '[role="banner"], [role="navigation"], [role="main"], [role="complementary"], ' +
                    '[role="contentinfo"], [role="search"], [role="form"], [role="region"], ' +
                    'header, nav, main, aside, footer'
                )).map(el => ({
                    tag: el.tagName.toLowerCase(),
                    role: el.getAttribute('role') || el.tagName.toLowerCase(),
                    aria_label: el.getAttribute('aria-label'),
                }));

                // Language
                const lang = document.documentElement.lang || '';

                // Page HTML (truncated)
                const html = document.documentElement.outerHTML.slice(0, 50000);

                // --- AA-relevant data ---

                // Viewport meta tag
                const viewportEl = document.querySelector('meta[name="viewport"]');
                const viewport_meta = viewportEl ? viewportEl.getAttribute('content') || '' : '';

                // Elements with tabindex (check for positive tabindex anti-pattern)
                const tabindex_elements = Array.from(document.querySelectorAll('[tabindex]'))
                    .slice(0, 100)
                    .map(el => ({
                        tag: el.tagName.toLowerCase(),
                        tabindex: parseInt(el.getAttribute('tabindex'), 10),
                        text: (el.textContent || '').trim().slice(0, 60),
                        role: el.getAttribute('role'),
                    }));

                // Inputs that should have autocomplete (personal data fields)
                const autocompleteTags = 'input[type="text"], input[type="email"], input[type="tel"], input[type="url"], input[type="password"], input[type="search"]';
                const autocomplete_inputs = Array.from(document.querySelectorAll(autocompleteTags))
                    .slice(0, 50)
                    .map(input => ({
                        tag: input.tagName.toLowerCase(),
                        type: input.type,
                        name: input.name,
                        id: input.id,
                        autocomplete: input.getAttribute('autocomplete') || '',
                        aria_label: input.getAttribute('aria-label'),
                        placeholder: input.placeholder,
                    }));

                // Sample text elements for contrast / spacing checks
                const textTags = 'p, span, li, td, th, label, a, h1, h2, h3, h4, h5, h6, div, button';
                const text_samples = Array.from(document.querySelectorAll(textTags))
                    .filter(el => el.textContent.trim().length > 0)
                    .slice(0, 60)
                    .map(el => {
                        const style = window.getComputedStyle(el);
                        return {
                            tag: el.tagName.toLowerCase(),
                            text: el.textContent.trim().slice(0, 80),
                            color: style.color,
                            background_color: style.backgroundColor,
                            font_size: style.fontSize,
                            font_weight: style.fontWeight,
                            line_height: style.lineHeight,
                            letter_spacing: style.letterSpacing,
                            selector: el.id ? el.tagName.toLowerCase() + '#' + el.id : el.tagName.toLowerCase(),
                        };
                    });

                // Focus styles: check if interactive elements have visible focus indicators
                const focusCheckElements = Array.from(document.querySelectorAll(
                    'a, button, input, select, textarea, [tabindex="0"], [role="button"]'
                )).slice(0, 30);
                const focus_styles = focusCheckElements.map(el => {
                    const style = window.getComputedStyle(el);
                    return {
                        tag: el.tagName.toLowerCase(),
                        text: (el.textContent || '').trim().slice(0, 60),
                        outline_style: style.outlineStyle,
                        outline_width: style.outlineWidth,
                        outline_color: style.outlineColor,
                        has_outline_none: style.outlineStyle === 'none' && style.outlineWidth === '0px',
                    };
                });

                // Elements with lang attribute (language of parts)
                const lang_parts = Array.from(document.querySelectorAll('[lang]'))
                    .filter(el => el !== document.documentElement)
                    .slice(0, 50)
                    .map(el => ({
                        tag: el.tagName.toLowerCase(),
                        lang: el.getAttribute('lang'),
                        text: el.textContent.trim().slice(0, 80),
                    }));

                // ARIA live regions (for status messages check)
                const aria_live_regions = Array.from(document.querySelectorAll(
                    '[aria-live], [role="alert"], [role="status"], [role="log"], [role="marquee"], [role="timer"]'
                )).slice(0, 20).map(el => ({
                    tag: el.tagName.toLowerCase(),
                    role: el.getAttribute('role'),
                    aria_live: el.getAttribute('aria-live'),
                    text: el.textContent.trim().slice(0, 100),
                }));

                // Duplicate IDs (violates WCAG 4.1.1)
                const allIds = Array.from(document.querySelectorAll('[id]')).map(el => el.id);
                const idCounts = {};
                allIds.forEach(id => { idCounts[id] = (idCounts[id] || 0) + 1; });
                const duplicate_ids = Object.entries(idCounts)
                    .filter(([_, count]) => count > 1)
                    .slice(0, 30)
                    .map(([id, count]) => ({ id, count }));

                return {
                    headings, images, forms, links,
                    interactive_elements: interactive, landmarks, lang, html,
                    viewport_meta, tabindex_elements, autocomplete_inputs,
                    text_samples, focus_styles, lang_parts,
                    aria_live_regions, duplicate_ids,
                };
            }""")
            return data
        except Exception as e:
            logger.error("page_data_extraction_error", error=str(e))
            return {}

    async def _compute_content_hash(self, page: Page) -> str:
        """Compute a hash of the page's meaningful content for deduplication."""
        try:
            content = await page.evaluate("""() => {
                // Use text content + structure for hashing, ignoring dynamic elements
                const main = document.querySelector('main') || document.body;
                const structure = Array.from(main.querySelectorAll('*'))
                    .slice(0, 500)
                    .map(el => el.tagName)
                    .join(',');
                const text = main.textContent.trim().slice(0, 5000);
                return structure + '|' + text;
            }""")
            return hashlib.sha256(content.encode()).hexdigest()[:16]
        except Exception:
            return hashlib.sha256(page.url.encode()).hexdigest()[:16]

    async def _extract_element_bounding_boxes(self, page: Page) -> list[dict]:
        """Extract bounding boxes for key interactive and visual elements.

        Returns a list of dicts with selector, tag, text, alt, aria_label, role,
        and bbox {x, y, width, height} for each visible element.
        """
        try:
            elements = await page.evaluate("""() => {
                const selectors = 'img, button, [role="button"], a, input, select, textarea, [role="img"], [role="link"], [role="checkbox"], [role="radio"]';
                const els = Array.from(document.querySelectorAll(selectors));
                const results = [];

                for (const el of els) {
                    const rect = el.getBoundingClientRect();
                    // Skip invisible elements
                    if (rect.width === 0 || rect.height === 0) continue;

                    // Build a unique CSS selector
                    let selector = el.tagName.toLowerCase();
                    if (el.id) {
                        selector += '#' + CSS.escape(el.id);
                    } else {
                        // Use nth-child for uniqueness
                        const parent = el.parentElement;
                        if (parent) {
                            const siblings = Array.from(parent.children);
                            const idx = siblings.indexOf(el) + 1;
                            selector += ':nth-child(' + idx + ')';
                        }
                        // Prepend parent tag for more specificity
                        if (parent && parent !== document.body && parent !== document.documentElement) {
                            let parentSel = parent.tagName.toLowerCase();
                            if (parent.id) {
                                parentSel += '#' + CSS.escape(parent.id);
                            }
                            selector = parentSel + ' > ' + selector;
                        }
                    }

                    // Use scroll offsets to get page-absolute coordinates
                    // (full_page screenshot captures the entire scrollable area)
                    const scrollX = window.scrollX || window.pageXOffset;
                    const scrollY = window.scrollY || window.pageYOffset;

                    results.push({
                        selector: selector,
                        tag: el.tagName.toLowerCase(),
                        text: (el.textContent || '').trim().slice(0, 100),
                        alt: el.getAttribute('alt'),
                        aria_label: el.getAttribute('aria-label'),
                        role: el.getAttribute('role'),
                        bbox: {
                            x: Math.round(rect.x + scrollX),
                            y: Math.round(rect.y + scrollY),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height),
                        },
                    });

                    if (results.length >= 150) break;
                }
                return results;
            }""")
            return elements
        except Exception as e:
            logger.warning("bounding_box_extraction_error", error=str(e))
            return []
