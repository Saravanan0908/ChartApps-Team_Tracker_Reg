"""Global test runner configuration and profile paths."""

import os
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
USER_DATA_DIR = BASE_DIR / ".auth_profile"
STORAGE_STATE_PATH = USER_DATA_DIR / "storage_state.json"

# Browser Configuration (Default to Headed locally for Codegen/debugging; Headless in CI)
HEADLESS: bool = (os.environ.get("HEADLESS", "").lower() in ("true", "1")) or bool(os.environ.get("CI"))
SLOW_MO_MS: int = 0
CHANNEL: str = "chrome" if (not os.environ.get("CI") and not os.environ.get("USE_CHROMIUM")) else ""
DEFAULT_TIMEOUT_MS: int = 30000
AUTH_SETUP_TIMEOUT_MS: int = 180000
