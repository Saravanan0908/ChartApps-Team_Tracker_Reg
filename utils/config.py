"""Global test runner configuration and profile paths."""

import os
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
USER_DATA_DIR = BASE_DIR / ".auth_profile"
STORAGE_STATE_PATH = USER_DATA_DIR / "storage_state.json"

# Browser Configuration (Default to Headless mode; use HEADED=true for debugging)
HEADLESS: bool = os.environ.get("HEADED", "").lower() not in ("true", "1")
SLOW_MO_MS: int = 0

def _get_browser_channel() -> str:
    """Use official Google Chrome by default locally, Chromium in CI."""
    if os.environ.get("CI") or os.environ.get("USE_CHROMIUM"):
        return ""
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    for p in chrome_paths:
        if os.path.exists(p):
            return "chrome"
    return "chrome"

CHANNEL: str = _get_browser_channel()

# Realistic desktop Chrome User-Agent to prevent Google OAuth detection (eliminates "HeadlessChrome")
REAL_USER_AGENT: str = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

DEFAULT_TIMEOUT_MS: int = 30000
AUTH_SETUP_TIMEOUT_MS: int = 180000
