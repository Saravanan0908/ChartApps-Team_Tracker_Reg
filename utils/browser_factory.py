"""Browser factory for launching Playwright with persistent context and anti-detection settings."""

from pathlib import Path
from typing import Optional, Tuple
from playwright.sync_api import Browser, BrowserContext, Page, Playwright
from utils.config import CHANNEL, HEADLESS, SLOW_MO_MS, USER_DATA_DIR, STORAGE_STATE_PATH


def launch_persistent_browser(
    playwright: Playwright,
    user_data_dir: Optional[Path] = None,
    headless: bool = HEADLESS,
    channel: Optional[str] = CHANNEL,
) -> Tuple[BrowserContext, Page]:
    """Launch browser with a persistent profile to retain Google & ChartApps sessions.
    
    This preserves cookies, local storage, and Google authentication between runs,
    and strips the automation flags that trigger bot detection.
    """
    profile_dir = Path(user_data_dir or USER_DATA_DIR)
    profile_dir.mkdir(parents=True, exist_ok=True)

    launch_kwargs = {
        "user_data_dir": str(profile_dir),
        "headless": headless,
        "args": [
            "--disable-blink-features=AutomationControlled",
        ],
        "ignore_default_args": ["--enable-automation"],
    }
    if not headless:
        launch_kwargs["args"].append("--start-maximized")
        launch_kwargs["no_viewport"] = True
    if channel:
        launch_kwargs["channel"] = channel

    # Load storage_state.json if present (crucial for CI environments)
    storage_state_file = profile_dir / "storage_state.json"
    if storage_state_file.exists():
        launch_kwargs["storage_state"] = str(storage_state_file)
    elif STORAGE_STATE_PATH.exists():
        launch_kwargs["storage_state"] = str(STORAGE_STATE_PATH)

    context = playwright.chromium.launch_persistent_context(**launch_kwargs)
    page = context.pages[0] if context.pages else context.new_page()
    return context, page


def create_browser_and_page(
    playwright: Playwright,
    headless: bool = HEADLESS,
    channel: Optional[str] = CHANNEL,
) -> Tuple[Browser, BrowserContext, Page]:
    """Launch standard browser instance (clean session)."""
    launch_kwargs = {
        "headless": headless,
        "args": ["--disable-blink-features=AutomationControlled"],
        "ignore_default_args": ["--enable-automation"],
    }
    if channel:
        launch_kwargs["channel"] = channel

    browser: Browser = playwright.chromium.launch(**launch_kwargs)
    context: BrowserContext = browser.new_context()
    page: Page = context.new_page()
    return browser, context, page
