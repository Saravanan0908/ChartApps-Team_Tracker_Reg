"""First Execution: One-Time Manual Setup for Google Authentication.

Workflow:
1. Launch ChartApps using installed Google Chrome with a persistent user profile (.auth_profile)
2. Click 'Connect Google' / 'Google Sign in with Google'
3. Wait for you to manually complete the Google login and authorization
4. Once completed and redirected back to the ChartApps dashboard, capture session & close
5. Retain profile so future runs are fully automated
"""

import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pages.login_page import LoginPage
from utils.browser_factory import launch_persistent_browser
from utils.config import AUTH_SETUP_TIMEOUT_MS, STORAGE_STATE_PATH, USER_DATA_DIR


def run_one_time_setup() -> None:
    print("=" * 60)
    print("STEP 1: Launching Google Chrome with persistent profile...")
    print(f"Profile directory: {USER_DATA_DIR}")
    print("=" * 60)

    with sync_playwright() as playwright:
        context, page = launch_persistent_browser(
            playwright,
            user_data_dir=USER_DATA_DIR,
            headless=False,
        )

        login_page = LoginPage(page)

        print("\nSTEP 2: Navigating to ChartApps...")
        login_page.open_auth_page()

        print("\nSTEP 3: Clicking 'Connect Google'...")
        if login_page.is_connect_google_visible():
            login_page.click_google_sign_in()
            print("Clicked Google Sign In button.")
        else:
            print("Already past initial auth screen.")

        print("\n" + "=" * 60)
        print("ACTION REQUIRED:")
        print("Please enter your Google Email, Password, and any 2FA in the opened Chrome window.")
        print("Once authorization finishes and you land on the ChartApps dashboard,")
        print("this script will automatically detect the completed login.")
        print("=" * 60 + "\n")

        # Automatically wait for login completion or give option to press Enter
        completed = False
        try:
            print("Waiting for redirection back to ChartApps dashboard...")
            completed = login_page.wait_for_auth_completion(timeout_ms=AUTH_SETUP_TIMEOUT_MS)
        except KeyboardInterrupt:
            print("\nSetup interrupted by user.")

        if not completed:
            # Fallback prompt in case redirection took longer
            user_input = input("Have you finished signing in and reached the dashboard? (y/n): ")
            completed = user_input.strip().lower() in ("y", "yes")

        if completed or login_page.is_authenticated():
            print("\n[SUCCESS] Authentication completed successfully!")
            # Save storage state snapshot as well
            STORAGE_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
            context.storage_state(path=str(STORAGE_STATE_PATH))
            print(f"Session state saved to: {STORAGE_STATE_PATH}")
            print(f"Persistent profile retained in: {USER_DATA_DIR}")
        else:
            print("\n[WARNING] Could not confirm dashboard redirect. Saved current profile state.")

        print("\nClosing browser...")
        context.close()
        print("Browser closed. One-time setup is complete!")
        print("Now you can run your automated tests anytime using: pytest or python tests/test_spreadsheet.py")


if __name__ == "__main__":
    run_one_time_setup()

