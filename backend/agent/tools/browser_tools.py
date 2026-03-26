from __future__ import annotations

from langchain_core.tools import tool


@tool
async def navigate_to_url(url: str) -> dict:
    """Navigate the browser to a specific URL.

    Args:
        url: The URL to navigate to

    Returns:
        Page info including title and URL
    """
    from crawler.action_executor import BrowserPool

    page = await BrowserPool.get_page()
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        return {
            "url": page.url,
            "title": await page.title(),
            "success": True,
        }
    except Exception as e:
        return {"url": url, "success": False, "error": str(e)}


@tool
async def click_element(selector: str) -> dict:
    """Click an element on the current page.

    Args:
        selector: CSS selector of the element to click

    Returns:
        Result of the click action
    """
    from crawler.action_executor import BrowserPool

    page = await BrowserPool.get_page()
    try:
        await page.click(selector, timeout=5000)
        await page.wait_for_load_state("networkidle", timeout=10000)
        return {
            "selector": selector,
            "success": True,
            "new_url": page.url,
        }
    except Exception as e:
        return {"selector": selector, "success": False, "error": str(e)}


@tool
async def take_screenshot(path: str | None = None) -> dict:
    """Take a screenshot of the current page.

    Args:
        path: Optional file path to save the screenshot

    Returns:
        Screenshot info including file path
    """
    import os
    import uuid
    from app.config import settings

    from crawler.action_executor import BrowserPool

    page = await BrowserPool.get_page()

    if not path:
        os.makedirs(settings.SCREENSHOT_DIR, exist_ok=True)
        path = os.path.join(settings.SCREENSHOT_DIR, f"{uuid.uuid4()}.png")

    try:
        await page.screenshot(path=path, full_page=True)
        return {"path": path, "success": True}
    except Exception as e:
        return {"path": path, "success": False, "error": str(e)}


@tool
async def get_page_accessibility_tree() -> dict:
    """Get the accessibility tree of the current page.

    Returns:
        Accessibility tree data
    """
    from crawler.action_executor import BrowserPool

    page = await BrowserPool.get_page()
    try:
        a11y_tree = await page.accessibility.snapshot()
        return {"a11y_tree": a11y_tree, "success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
async def get_page_html(selector: str = "body") -> dict:
    """Get the HTML content of a page element.

    Args:
        selector: CSS selector (default: body)

    Returns:
        HTML content of the element
    """
    from crawler.action_executor import BrowserPool

    page = await BrowserPool.get_page()
    try:
        html = await page.inner_html(selector)
        return {"html": html[:10000], "success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
