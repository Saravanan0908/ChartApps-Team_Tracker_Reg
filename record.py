"""Codegen recorder that allows Google sign-in (email & password) without bot detection."""

from pathlib import Path
from playwright.sync_api import sync_playwright

USER_DATA_DIR = Path(__file__).resolve().parent / ".auth_profile"
USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 65)
print("Launching Codegen Recorder with Google Anti-Bot bypass...")
print("=" * 65)

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir=str(USER_DATA_DIR),
        channel="chrome",
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
        ignore_default_args=["--enable-automation"],
        no_viewport=True,
    )
    page = context.pages[0] if context.pages else context.new_page()
    page.goto("https://chartapps.app/dashboard")
    
    # Opens the Playwright Inspector / Codegen recorder toolbar
    page.pause()

