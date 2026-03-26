from __future__ import annotations

import asyncio
from typing import Any

from playwright.async_api import async_playwright, Browser, Page, BrowserContext
import structlog

from app.config import settings

logger = structlog.get_logger()


class BrowserPool:
    """Manages a pool of Playwright browser instances for concurrent crawling."""

    _playwright = None
    _browser: Browser | None = None
    _contexts: list[BrowserContext] = []
    _available_pages: asyncio.Queue | None = None
    _lock = asyncio.Lock()

    @classmethod
    async def initialize(cls, pool_size: int = 3):
        """Initialize the browser pool with a set number of pages."""
        async with cls._lock:
            if cls._browser is not None:
                return

            cls._playwright = await async_playwright().start()
            cls._browser = await cls._playwright.chromium.launch(
                headless=True,
                args=[
                    "--disable-gpu",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-web-security",
                ],
            )

            cls._available_pages = asyncio.Queue()

            for i in range(pool_size):
                context = await cls._browser.new_context(
                    viewport={"width": 1280, "height": 720},
                    user_agent="W4Agent/1.0 Accessibility Checker",
                    ignore_https_errors=True,
                )
                cls._contexts.append(context)
                page = await context.new_page()
                await cls._available_pages.put(page)

            logger.info("browser_pool_initialized", pool_size=pool_size)

    @classmethod
    async def get_page(cls) -> Page:
        """Get an available page from the pool."""
        if cls._available_pages is None:
            await cls.initialize()
        return await cls._available_pages.get()

    @classmethod
    async def release_page(cls, page: Page):
        """Return a page to the pool."""
        if cls._available_pages is not None:
            await cls._available_pages.put(page)

    @classmethod
    async def shutdown(cls):
        """Close all browser instances and clean up."""
        async with cls._lock:
            for ctx in cls._contexts:
                try:
                    await ctx.close()
                except Exception:
                    pass
            cls._contexts.clear()

            if cls._browser:
                await cls._browser.close()
                cls._browser = None

            if cls._playwright:
                await cls._playwright.stop()
                cls._playwright = None

            cls._available_pages = None
            logger.info("browser_pool_shutdown")


class ActionExecutor:
    """Executes browser actions on a Playwright page."""

    def __init__(self, page: Page):
        self.page = page

    async def navigate(self, url: str, wait_until: str = "networkidle") -> dict:
        """Navigate to a URL and return page info."""
        try:
            response = await self.page.goto(
                url,
                wait_until=wait_until,
                timeout=settings.PAGE_TIMEOUT_MS,
            )
            return {
                "url": self.page.url,
                "title": await self.page.title(),
                "status": response.status if response else None,
                "success": True,
            }
        except Exception as e:
            logger.error("navigation_error", url=url, error=str(e))
            return {"url": url, "success": False, "error": str(e)}

    async def click(self, selector: str) -> dict:
        """Click an element and return the result."""
        try:
            await self.page.click(selector, timeout=5000)
            await self.page.wait_for_load_state("networkidle", timeout=10000)
            return {
                "selector": selector,
                "success": True,
                "new_url": self.page.url,
            }
        except Exception as e:
            return {"selector": selector, "success": False, "error": str(e)}

    async def fill(self, selector: str, value: str) -> dict:
        """Fill a form field."""
        try:
            await self.page.fill(selector, value, timeout=5000)
            return {"selector": selector, "value": value, "success": True}
        except Exception as e:
            return {"selector": selector, "success": False, "error": str(e)}

    async def scroll(self, direction: str = "down", amount: int = 500) -> dict:
        """Scroll the page."""
        try:
            if direction == "down":
                await self.page.evaluate(f"window.scrollBy(0, {amount})")
            elif direction == "up":
                await self.page.evaluate(f"window.scrollBy(0, -{amount})")
            return {"direction": direction, "amount": amount, "success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def take_screenshot(self, path: str) -> dict:
        """Take a full-page screenshot."""
        try:
            await self.page.screenshot(path=path, full_page=True)
            return {"path": path, "success": True}
        except Exception as e:
            return {"path": path, "success": False, "error": str(e)}

    async def get_accessibility_tree(self) -> dict | None:
        """Get the accessibility tree of the current page."""
        try:
            return await self.page.accessibility.snapshot()
        except Exception as e:
            logger.warning("a11y_tree_error", error=str(e))
            return None

    async def get_interactive_elements(self) -> list[dict]:
        """Get all interactive elements on the page."""
        try:
            elements = await self.page.evaluate("""() => {
                const interactiveSelectors = [
                    'a[href]', 'button', 'input', 'select', 'textarea',
                    '[role="button"]', '[role="link"]', '[role="tab"]',
                    '[role="menuitem"]', '[tabindex]', '[onclick]'
                ];
                const elements = [];
                for (const selector of interactiveSelectors) {
                    document.querySelectorAll(selector).forEach(el => {
                        const rect = el.getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0) {
                            elements.push({
                                tag: el.tagName.toLowerCase(),
                                type: el.type || null,
                                text: (el.textContent || '').trim().slice(0, 100),
                                href: el.href || null,
                                selector: el.id ? '#' + el.id :
                                    el.className ? el.tagName.toLowerCase() + '.' + el.className.split(' ')[0] :
                                    el.tagName.toLowerCase(),
                                aria_label: el.getAttribute('aria-label'),
                                role: el.getAttribute('role'),
                                visible: rect.width > 0 && rect.height > 0,
                            });
                        }
                    });
                }
                return elements;
            }""")
            return elements
        except Exception as e:
            logger.warning("get_elements_error", error=str(e))
            return []

    async def get_all_links(self, base_url: str) -> list[str]:
        """Get all links on the page, filtered to same-domain."""
        try:
            from urllib.parse import urlparse, urljoin

            links = await self.page.evaluate("""() => {
                return Array.from(document.querySelectorAll('a[href]'))
                    .map(a => a.href)
                    .filter(href => href && !href.startsWith('javascript:') && !href.startsWith('#'));
            }""")

            base_domain = urlparse(base_url).netloc
            filtered = []
            for link in links:
                parsed = urlparse(link)
                if parsed.netloc == base_domain or not parsed.netloc:
                    full_url = urljoin(base_url, link)
                    # Remove fragments
                    full_url = full_url.split('#')[0]
                    if full_url not in filtered:
                        filtered.append(full_url)

            return filtered
        except Exception as e:
            logger.warning("get_links_error", error=str(e))
            return []
