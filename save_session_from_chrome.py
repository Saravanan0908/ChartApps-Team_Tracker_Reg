"""Connect to the running Chrome on port 9222 and save storage_state.json."""

from pathlib import Path
from playwright.sync_api import sync_playwright

USER_DATA_DIR = Path(__file__).resolve().parent / ".auth_profile"
STORAGE_FILE = USER_DATA_DIR / "storage_state.json"

try:
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        STORAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
        context.storage_state(path=str(STORAGE_FILE))
        print(f"[SUCCESS] Authenticated session saved to: {STORAGE_FILE}")
except Exception as e:
    print(f"[ERROR] Could not connect to Chrome on port 9222: {e}")

