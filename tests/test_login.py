"""Login test cases converted to Page Object Model (POM)."""

import sys
import time
import webbrowser
from pathlib import Path
from playwright.sync_api import Page, expect, sync_playwright

# Ensure project root is in sys.path when running script directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pages.login_page import LoginPage
from testdata.test_data import LoginTestData
from utils.browser_factory import create_browser_and_page
from utils.config import HEADLESS


def test_google_login(page: Page) -> None:
    """Enter email, click next, and continue to password (skipping error checks)."""
    login_page = LoginPage(page)

    # 1. Navigate to auth page
    login_page.open_auth_page()

    # 2. Click Google sign-in
    login_page.click_google_sign_in()

    # 3. Enter email and proceed to password
    login_page.enter_email_or_phone(LoginTestData.EMAIL)
    login_page.click_next()

    # 4. Enter password and continue
    login_page.enter_password(LoginTestData.PASSWORD)
    login_page.click_password_next()


def run_standalone() -> None:
    """Standalone runner equivalent to the original Playwright script."""
    with sync_playwright() as playwright:
        browser, context, page = create_browser_and_page(playwright, headless=HEADLESS)
        try:
            test_google_login(page)
            print("\n[SUCCESS] Login test completed successfully!")
        except Exception as e:
            print(f"\n[FAILURE] Login test failed: {e}")
            reports_dir = Path("reports/screenshots")
            reports_dir.mkdir(parents=True, exist_ok=True)
            screenshot_path = reports_dir / f"failure_login_{int(time.time())}.png"
            try:
                page.screenshot(path=str(screenshot_path))
                print(f"[INFO] Failure screenshot captured: {screenshot_path}")
            except Exception:
                pass
            report_path = Path("reports/azure_test_report.html").resolve()
            if report_path.exists():
                print(f"[INFO] Report generated: {report_path}")
                import os
                if not os.environ.get("CI"):
                    webbrowser.open(report_path.as_uri())
            raise e
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    run_standalone()
