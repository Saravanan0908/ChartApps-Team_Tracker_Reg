"""Global test runner configuration and profile paths."""

from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
USER_DATA_DIR = BASE_DIR / ".auth_profile"
STORAGE_STATE_PATH = USER_DATA_DIR / "storage_state.json"

# Browser Configuration
HEADLESS: bool = False
SLOW_MO_MS: int = 0
CHANNEL: str = "chrome"  # Launch installed Google Chrome
DEFAULT_TIMEOUT_MS: int = 30000
AUTH_SETUP_TIMEOUT_MS: int = 180000  # 3 minutes for manual login setup
