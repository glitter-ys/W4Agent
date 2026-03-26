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
        """
        url = page.url
        title = await page.title()

        # Gather page data in parallel
        a11y_tree = await self._get_a11y_tree(page)
        page_data = await self._extract_page_data(page)
        content_hash = await self._compute_content_hash(page)

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

                return { headings, images, forms, links, interactive_elements: interactive, landmarks, lang, html };
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
