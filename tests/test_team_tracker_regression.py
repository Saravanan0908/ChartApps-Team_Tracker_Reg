"""Regression Test: Team Tracker Form Submission and Spreadsheet Data Storage.

Validates:
1. Dashboard navigation and modal handling
2. Navigation to Team Tracker and tracker view
3. Date picker selection using current date
4. Dynamic Task / Activity input with current date and runtime
5. Form submission and success confirmation ("Data added to the spreadsheet")
6. Verification that submitted data is stored and visible in the spreadsheet table
"""

import sys
import time
import webbrowser
from pathlib import Path
import pytest
from playwright.sync_api import Page, sync_playwright

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pages.team_tracker_page import TeamTrackerPage
from testdata.team_tracker_data import TeamTrackerTestData
from utils.browser_factory import launch_persistent_browser
from utils.config import HEADLESS, USER_DATA_DIR


@pytest.mark.regression
def test_form_submission_and_data_stored(persistent_page: Page) -> None:
    """Regression test for submitting a task with current date and validating spreadsheet storage."""
    team_tracker_page = TeamTrackerPage(persistent_page)

    # 1. Open Dashboard and close any introductory modal
    team_tracker_page.open_dashboard()
    team_tracker_page.close_modal_if_present()

    # 2. Navigate to Team Tracker section
    team_tracker_page.navigate_to_team_tracker()

    # 3. Open the Tracker View
    team_tracker_page.open_tracker_view()

    # 4. Generate dynamic test data with current date & run time
    form_data = TeamTrackerTestData.get_form_payload(option="FN")
    current_date = form_data["date"]
    task_description = form_data["task_description"]
    activity_text = form_data["activity"]

    print(f"\n[INFO] Submitting Date: {current_date}")
    print(f"[INFO] Submitting Task: {task_description}")
    print(f"[INFO] Submitting Activity: {activity_text}")

    # 5. Fill Date Picker with Current Date
    team_tracker_page.select_date(current_date)

    # 6. Select Shift/Option dropdown
    team_tracker_page.select_option(form_data["option"])

    # 7. Fill Task and Activity descriptions with Current Date & Run Time
    team_tracker_page.fill_task_and_activity(
        task_description=task_description,
        activity_text=activity_text,
    )

    # 8. Submit Form
    team_tracker_page.submit_form()

    # 9. Verify Success Confirmation
    team_tracker_page.verify_success_toast()
    print("[PASS] Verified success toast: 'Data added to the spreadsheet'")

    # 10. Sort table by Date to reveal newest entry
    team_tracker_page.sort_table_by_date()

    # 11. Verify submitted Task & Activity are stored in the Spreadsheet Table
    team_tracker_page.verify_data_stored_in_table(
        task_description=task_description,
        activity_text=activity_text,
    )
    print("[PASS] Verified submitted data is stored and displayed in spreadsheet table!")


def run_standalone() -> None:
    """Run directly from command line in headless mode and exit automatically."""
    print("=" * 65)
    print(f"Running Regression Test (Headless: {HEADLESS})...")
    print("=" * 65)

    with sync_playwright() as playwright:
        context, page = launch_persistent_browser(
            playwright,
            user_data_dir=USER_DATA_DIR,
            headless=HEADLESS,
        )
        try:
            test_form_submission_and_data_stored(page)
            print("\n[SUCCESS] Regression Test Completed Successfully!")
        except Exception as e:
            print(f"\n[FAILURE] Regression test failed: {e}")
            reports_dir = Path("reports/screenshots")
            reports_dir.mkdir(parents=True, exist_ok=True)
            screenshot_path = reports_dir / f"failure_regression_{int(time.time())}.png"
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
