"""Subsequent Executions: Reusing the authenticated Google session.

Workflow:
1. Launch Playwright with retained profile (.auth_profile)
2. Open ChartApps dashboard
3. Click Connect Google (auto-connects using retained Google session)
4. Verify session is valid (no auth blockage)
5. Validate spreadsheet operations
"""

import sys
import time
import webbrowser
from pathlib import Path
from playwright.sync_api import Page, expect, sync_playwright

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pages.spreadsheet_page import SpreadsheetPage
from utils.browser_factory import launch_persistent_browser
from utils.config import USER_DATA_DIR


def test_spreadsheet_operations_with_saved_session(persistent_page: Page) -> None:
    """Validate spreadsheet access and operations using the retained Google session."""
    spreadsheet_page = SpreadsheetPage(persistent_page)

    # 1. Open ChartApps
    spreadsheet_page.open()

    # 2. Reconnect Google if session prompt appears
    spreadsheet_page.connect_google_if_needed()

    # 3. Assert existing session is valid and not stuck on auth screen
    expect(persistent_page).not_to_have_url(r".*/dashboard/auth.*")

    # 4. Validate spreadsheet operations and view
    is_valid = spreadsheet_page.validate_spreadsheet_operations()
    assert is_valid, "Spreadsheet container/dashboard should be rendered and accessible"


def run_standalone() -> None:
    """Run directly from command line."""
    print("=" * 60)
    print("Running automated spreadsheet test using retained session...")
    print("=" * 60)

    with sync_playwright() as playwright:
        context, page = launch_persistent_browser(
            playwright,
            user_data_dir=USER_DATA_DIR,
            headless=False,
        )
        try:
            spreadsheet_page = SpreadsheetPage(page)
            spreadsheet_page.open()
            spreadsheet_page.connect_google_if_needed()
            expect(page).not_to_have_url(r".*/dashboard/auth.*")
            is_valid = spreadsheet_page.validate_spreadsheet_operations()
            assert is_valid, "Spreadsheet container/dashboard should be rendered and accessible"
            print("[PASS] Spreadsheet operations validated successfully with retained Google session!")
            
            # Keep browser open after completion
            print("\n" + "=" * 65)
            print("[SUCCESS] All steps completed! The browser will remain open.")
            print("Press Enter in this terminal whenever you want to close it...")
            print("=" * 65)
            input()
        except Exception as e:
            print(f"\n[FAILURE] Test failed: {e}")
            reports_dir = Path("reports/screenshots")
            reports_dir.mkdir(parents=True, exist_ok=True)
            screenshot_path = reports_dir / f"failure_spreadsheet_{int(time.time())}.png"
            try:
                page.screenshot(path=str(screenshot_path))
                print(f"[INFO] Failure screenshot captured: {screenshot_path}")
            except Exception:
                pass
            report_path = Path("reports/azure_test_report.html").resolve()
            if report_path.exists():
                print(f"[INFO] Opening report: {report_path}")
                webbrowser.open(report_path.as_uri())
            raise e
        finally:
            context.close()


if __name__ == "__main__":
    run_standalone()
