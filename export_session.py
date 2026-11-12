"""Helper script to export your logged-in session to storage_state.json for GitHub Actions."""

import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from utils.config import USER_DATA_DIR, STORAGE_STATE_PATH


def export_session() -> None:
    print("=" * 65)
    print("Exporting Authenticated Session for GitHub Actions...")
    print(f"Profile directory: {USER_DATA_DIR}")
    print("=" * 65)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(USER_DATA_DIR),
            channel="chrome",
            headless=True,
        )
        STORAGE_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        context.storage_state(path=str(STORAGE_STATE_PATH))
        context.close()

    print(f"\n[SUCCESS] Session saved to: {STORAGE_STATE_PATH}")
    print("\n" + "=" * 65)
    print("HOW TO ADD TO GITHUB SECRETS:")
    print("1. Open the file below and copy its ENTIRE text content:")
    print(f"   {STORAGE_STATE_PATH.resolve()}")
    print("2. Go to your GitHub repository:")
    print("   https://github.com/Saravanan0908/ChartApps-Team_Tracker_Reg/settings/secrets/actions")
    print("3. Click 'New repository secret'")
    print("4. Name:  AUTH_STORAGE_STATE")
    print("5. Value: <Paste the copied JSON text>")
    print("6. Click 'Add secret'")
    print("=" * 65)


if __name__ == "__main__":
    export_session()

