"""Browser factory for launching Playwright with persistent context and anti-detection settings."""

from pathlib import Path
from typing import Optional, Tuple
from playwright.sync_api import Browser, BrowserContext, Page, Playwright
from utils.config import CHANNEL, HEADLESS, SLOW_MO_MS, USER_DATA_DIR


def launch_persistent_browser(
    playwright: Playwright,
    user_data_dir: Optional[Path] = None,
    headless: bool = HEADLESS,
    channel: str = CHANNEL,
) -> Tuple[BrowserContext, Page]:
    """Launch installed Google Chrome with a persistent profile to retain Google & ChartApps sessions.
    
    This preserves cookies, local storage, and Google authentication between runs,
    and strips the automation flags that trigger bot detection.
    """
    profile_dir = Path(user_data_dir or USER_DATA_DIR)
    profile_dir.mkdir(parents=True, exist_ok=True)

    context = playwright.chromium.launch_persistent_context(
        user_data_dir=str(profile_dir),
        channel=channel,
        headless=headless,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--start-maximized",
        ],
        ignore_default_args=["--enable-automation"],
        no_viewport=True,
    )

    page = context.pages[0] if context.pages else context.new_page()
    return context, page


def create_browser_and_page(
    playwright: Playwright,
    headless: bool = HEADLESS,
) -> Tuple[Browser, BrowserContext, Page]:
    """Launch standard browser instance (clean session)."""
    browser: Browser = playwright.chromium.launch(
        channel=CHANNEL,
        headless=headless,
        args=["--disable-blink-features=AutomationControlled"],
        ignore_default_args=["--enable-automation"],
    )
    context: BrowserContext = browser.new_context()
    page: Page = context.new_page()
    return browser, context, page
