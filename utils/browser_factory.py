"""Browser factory for launching Playwright with persistent context and anti-detection settings."""

import os
import json

# Suppress Playwright Inspector, recorder, and debug mode completely
import utils.suppress_debug

from pathlib import Path
from typing import Optional, Tuple
from playwright.sync_api import Browser, BrowserContext, Page, Playwright
from utils.config import CHANNEL, HEADLESS, REAL_USER_AGENT, SLOW_MO_MS, USER_DATA_DIR, STORAGE_STATE_PATH


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
        "user_agent": REAL_USER_AGENT,
        "args": [
            "--disable-blink-features=AutomationControlled",
            "--no-default-browser-check",
            "--disable-features=IsolateOrigins,site-per-process",
            "--disable-infobars",
            "--lang=en-US,en",
        ],
        "ignore_default_args": ["--enable-automation"],
    }
    if not headless:
        launch_kwargs["args"].extend([
            "--start-maximized",
            "--window-position=0,0",
        ])
        launch_kwargs["no_viewport"] = True
    else:
        launch_kwargs["viewport"] = {"width": 1920, "height": 1080}
    if channel:
        launch_kwargs["channel"] = channel

    # Note: launch_persistent_context does not take 'storage_state' as a parameter;
    # it uses the SQLite database in user_data_dir.
    context = playwright.chromium.launch_persistent_context(**launch_kwargs)

    # Inject saved cookies and localStorage from storage_state.json if available
    storage_state_file = profile_dir / "storage_state.json"
    target_state = storage_state_file if storage_state_file.exists() else (STORAGE_STATE_PATH if STORAGE_STATE_PATH.exists() else None)
    if not (target_state and target_state.exists()):
        repo_fallback = Path(__file__).resolve().parent.parent / "testdata" / "auth_session.json"
        if repo_fallback.exists():
            target_state = repo_fallback
            print(f"[INFO] Using repository session fallback: {repo_fallback}")
    if target_state:
        try:
            with open(target_state, "r", encoding="utf-8") as f:
                state_data = json.load(f)
                cookies = state_data.get("cookies", [])
                if cookies:
                    import time
                    now = time.time()
                    valid_cookies = [
                        c for c in cookies
                        if c.get("expires", -1) in (-1, None) or c.get("expires", 0) > now
                    ]
                    if valid_cookies:
                        context.add_cookies(valid_cookies)

                # Inject localStorage entries
                for origin_data in state_data.get("origins", []):
                    origin = origin_data.get("origin")
                    items = origin_data.get("localStorage", [])
                    if origin and items:
                        set_items = "; ".join([
                            f"window.localStorage.setItem({json.dumps(it['name'])}, {json.dumps(it['value'])});"
                            for it in items
                        ])
                        context.add_init_script(f"""
                            try {{
                                if (window.location.origin === {json.dumps(origin)}) {{
                                    {set_items}
                                }}
                            }} catch (e) {{}}
                        """)
        except Exception as e:
            print(f"[WARNING] Could not load cookies/localStorage from {target_state}: {e}")

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
        "args": [
            "--disable-blink-features=AutomationControlled",
            "--no-default-browser-check",
            "--disable-features=IsolateOrigins,site-per-process",
            "--disable-infobars",
            "--lang=en-US,en",
        ],
        "ignore_default_args": ["--enable-automation"],
    }
    context_kwargs = {
        "user_agent": REAL_USER_AGENT,
    }
    if not headless:
        launch_kwargs["args"].extend([
            "--start-maximized",
            "--window-position=0,0",
        ])
        context_kwargs["no_viewport"] = True
    else:
        context_kwargs["viewport"] = {"width": 1920, "height": 1080}

    if channel:
        launch_kwargs["channel"] = channel

    browser: Browser = playwright.chromium.launch(**launch_kwargs)
    context: BrowserContext = browser.new_context(**context_kwargs)
    page: Page = context.new_page()
    return browser, context, page
