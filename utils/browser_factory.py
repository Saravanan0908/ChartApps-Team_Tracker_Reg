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

    # Record video for failure capture & reporting
    videos_dir = Path("reports/videos")
    videos_dir.mkdir(parents=True, exist_ok=True)
    launch_kwargs["record_video_dir"] = str(videos_dir)
    launch_kwargs["record_video_size"] = {"width": 1280, "height": 720}

    # Note: launch_persistent_context does not take 'storage_state' as a parameter;
    # it uses the SQLite database in user_data_dir.
    context = playwright.chromium.launch_persistent_context(**launch_kwargs)

    # Anti-bot stealth initialization: properly delete navigator.webdriver and populate chrome runtime
    context.add_init_script("""
        try {
            const newProto = Object.getPrototypeOf(navigator);
            delete newProto.webdriver;
        } catch (e) {}
        try {
            delete navigator.webdriver;
        } catch (e) {}
        try {
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
                configurable: true
            });
        } catch (e) {}

        if (!window.chrome) {
            window.chrome = {};
        }
        if (!window.chrome.runtime) {
            window.chrome.runtime = {
                PlatformOs: { WIN: 'win', MAC: 'mac', ANDROID: 'android', LINUX: 'linux' },
                PlatformArch: { X86_64: 'x86-64', ARM64: 'arm64' },
                OnInstalledReason: { CHROME_UPDATE: 'chrome_update' }
            };
        }
    """)

    # Inject saved cookies and localStorage from storage_state.json if available
    storage_state_file = profile_dir / "storage_state.json"
    target_state = storage_state_file if storage_state_file.exists() else (STORAGE_STATE_PATH if STORAGE_STATE_PATH.exists() else None)
    if target_state:
        try:
            with open(target_state, "r", encoding="utf-8") as f:
                state_data = json.load(f)
                cookies = state_data.get("cookies", [])
                if cookies:
                    context.add_cookies(cookies)

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

    # Maximize the OS window via Chrome DevTools Protocol when running in headed mode
    if not headless:
        try:
            cdp = context.new_cdp_session(page)
            win = cdp.send("Browser.getWindowForTarget")
            if win and "windowId" in win:
                cdp.send("Browser.setWindowBounds", {
                    "windowId": win["windowId"],
                    "bounds": {"windowState": "maximized"},
                })
        except Exception:
            pass

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
    context.add_init_script("""
        try {
            const newProto = Object.getPrototypeOf(navigator);
            delete newProto.webdriver;
        } catch (e) {}
        try {
            delete navigator.webdriver;
        } catch (e) {}
        try {
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
                configurable: true
            });
        } catch (e) {}

        if (!window.chrome) {
            window.chrome = {};
        }
        if (!window.chrome.runtime) {
            window.chrome.runtime = {
                PlatformOs: { WIN: 'win', MAC: 'mac', ANDROID: 'android', LINUX: 'linux' },
                PlatformArch: { X86_64: 'x86-64', ARM64: 'arm64' },
                OnInstalledReason: { CHROME_UPDATE: 'chrome_update' }
            };
        }
    """)
    page: Page = context.new_page()

    # Maximize the OS window via Chrome DevTools Protocol when running in headed mode
    if not headless:
        try:
            cdp = context.new_cdp_session(page)
            win = cdp.send("Browser.getWindowForTarget")
            if win and "windowId" in win:
                cdp.send("Browser.setWindowBounds", {
                    "windowId": win["windowId"],
                    "bounds": {"windowState": "maximized"},
                })
        except Exception:
            pass

    return browser, context, page
