from __future__ import annotations

import json
from typing import Any

from playwright.async_api import Page
import structlog

from app.services.notification_service import NotificationService

logger = structlog.get_logger()


class EventType:
    COOKIE_CONSENT = "cookie_consent"
    POPUP = "popup"
    MODAL = "modal"
    ADVERTISEMENT = "advertisement"
    PERMISSION_REQUEST = "permission_request"
    LOGIN_WALL = "login_wall"
    CAPTCHA = "captcha"
    ALERT = "alert"
    UNKNOWN = "unknown"


# Common selectors for dismissing interrupting elements
DISMISS_PATTERNS = {
    EventType.COOKIE_CONSENT: [
        "button:has-text('Accept')",
        "button:has-text('接受')",
        "button:has-text('同意')",
        "button:has-text('OK')",
        "button:has-text('Got it')",
        "button:has-text('I agree')",
        "[class*='cookie'] button",
        "[id*='cookie'] button",
        "[class*='consent'] button",
        "[class*='gdpr'] button",
    ],
    EventType.POPUP: [
        "button:has-text('Close')",
        "button:has-text('关闭')",
        "button:has-text('×')",
        "[class*='close']",
        "[aria-label='Close']",
        "[aria-label='关闭']",
        ".modal-close",
        ".popup-close",
    ],
    EventType.ADVERTISEMENT: [
        "[class*='ad-close']",
        "[class*='ad'] [class*='close']",
        "[id*='ad'] button",
        "button:has-text('Skip')",
        "button:has-text('跳过')",
    ],
}


class EventResponder:
    """Detects and handles unexpected UI events during crawling.

    Monitors for popups, cookie banners, ads, login walls, and other
    interrupting elements. Attempts to dismiss them to keep the main
    detection flow running.
    """

    def __init__(self, task_id: str):
        self.task_id = task_id
        self._handled_events: list[dict] = []

    async def check_and_handle(self, page: Page) -> list[dict]:
        """Check for and handle any unexpected UI events on the page.

        Returns a list of detected and handled events.
        """
        events = []

        # Check for common overlay/modal elements
        detectors = [
            self._detect_cookie_consent,
            self._detect_popup_modal,
            self._detect_advertisement,
            self._detect_alert_dialog,
        ]

        for detector in detectors:
            try:
                event = await detector(page)
                if event:
                    events.append(event)
                    handled = await self._handle_event(page, event)
                    event["handled"] = handled

                    # Notify via WebSocket
                    await NotificationService.notify_event_detected(
                        self.task_id,
                        event["type"],
                        "dismissed" if handled else "could_not_dismiss",
                    )
            except Exception as e:
                logger.warning("event_detection_error", error=str(e))

        self._handled_events.extend(events)
        return events

    async def _detect_cookie_consent(self, page: Page) -> dict | None:
        """Detect cookie consent banners."""
        selectors = [
            "[class*='cookie']",
            "[id*='cookie']",
            "[class*='consent']",
            "[class*='gdpr']",
            "[aria-label*='cookie']",
        ]

        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element and await element.is_visible():
                    return {
                        "type": EventType.COOKIE_CONSENT,
                        "selector": selector,
                        "description": "Cookie consent banner detected",
                    }
            except Exception:
                continue
        return None

    async def _detect_popup_modal(self, page: Page) -> dict | None:
        """Detect popup/modal dialogs."""
        selectors = [
            "[role='dialog']",
            "[role='alertdialog']",
            ".modal.show",
            ".modal.active",
            "[class*='popup'][class*='show']",
            "[class*='overlay'][class*='visible']",
        ]

        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element and await element.is_visible():
                    return {
                        "type": EventType.POPUP,
                        "selector": selector,
                        "description": "Popup/modal dialog detected",
                    }
            except Exception:
                continue
        return None

    async def _detect_advertisement(self, page: Page) -> dict | None:
        """Detect advertisement overlays."""
        try:
            ad_detected = await page.evaluate("""() => {
                const adSelectors = [
                    '[class*="ad-overlay"]',
                    '[class*="interstitial"]',
                    '[id*="ad-container"]',
                    'iframe[src*="doubleclick"]',
                    'iframe[src*="googlesyndication"]',
                ];
                for (const sel of adSelectors) {
                    const el = document.querySelector(sel);
                    if (el && el.offsetWidth > 0 && el.offsetHeight > 0) {
                        return { selector: sel, found: true };
                    }
                }
                return { found: false };
            }""")

            if ad_detected.get("found"):
                return {
                    "type": EventType.ADVERTISEMENT,
                    "selector": ad_detected["selector"],
                    "description": "Advertisement overlay detected",
                }
        except Exception:
            pass
        return None

    async def _detect_alert_dialog(self, page: Page) -> dict | None:
        """Detect native JavaScript alert dialogs."""
        # Playwright handles alerts via dialog events; this is for custom alerts
        try:
            alert = await page.query_selector("[role='alert']")
            if alert and await alert.is_visible():
                text = await alert.text_content()
                return {
                    "type": EventType.ALERT,
                    "selector": "[role='alert']",
                    "description": f"Alert detected: {(text or '').strip()[:100]}",
                }
        except Exception:
            pass
        return None

    async def _handle_event(self, page: Page, event: dict) -> bool:
        """Attempt to dismiss/handle a detected event.

        Returns True if the event was successfully handled.
        """
        event_type = event["type"]
        dismiss_selectors = DISMISS_PATTERNS.get(event_type, []) + DISMISS_PATTERNS.get(EventType.POPUP, [])

        for selector in dismiss_selectors:
            try:
                button = await page.query_selector(selector)
                if button and await button.is_visible():
                    await button.click(timeout=3000)
                    # Wait for the element to be dismissed
                    await page.wait_for_timeout(500)
                    logger.info(
                        "event_dismissed",
                        type=event_type,
                        selector=selector,
                    )
                    return True
            except Exception:
                continue

        # Try pressing Escape as fallback
        try:
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(300)
            logger.info("event_dismissed_via_escape", type=event_type)
            return True
        except Exception:
            pass

        logger.warning("event_not_dismissed", type=event_type)
        return False

    @property
    def handled_events(self) -> list[dict]:
        return self._handled_events

    @property
    def event_count(self) -> int:
        return len(self._handled_events)
