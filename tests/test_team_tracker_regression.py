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
from utils.step_logger import StepLogger


@pytest.mark.regression
@pytest.mark.existing_app
def test_form_submission_and_data_stored(persistent_page: Page) -> None:
    """Regression test for submitting a task with current date and validating spreadsheet storage."""
    logger = StepLogger(suite_name="Team Tracker Regression Test", total_steps=11)
    logger.start_suite()
    team_tracker_page = TeamTrackerPage(persistent_page)

    try:
        # Step 1: Open Dashboard
        logger.step(1, "Open ChartApps Dashboard & Verify Session", "Navigating to /dashboard and checking authentication")
        team_tracker_page.open_dashboard()
        logger.passed(1, "Dashboard reached and session validated")

        # Step 2: Dismiss announcement modal
        logger.step(2, "Check & Dismiss Announcement Modal", "Looking for introductory popup/modal")
        team_tracker_page.close_modal_if_present()
        logger.passed(2, "Modal check finished")

        # Step 3: Navigate to Team Tracker
        logger.step(3, "Navigate to Team Tracker", "Locating 'My Apps' and clicking 'Team Tracker' link")
        team_tracker_page.navigate_to_team_tracker()
        logger.passed(3, "Navigated to Team Tracker section")

        # Step 4: Open Tracker View
        logger.step(4, "Open Tracker Card View", "Clicking 'View' on default tracker card")
        team_tracker_page.open_tracker_view()
        logger.passed(4, "Tracker view opened successfully")

        # Step 5: Generate dynamic test data
        logger.step(5, "Generate Dynamic Test Data", "Injecting current date (YYYY-MM-DD) and runtime (HH:MM:SS)")
        form_data = TeamTrackerTestData.get_form_payload(option="FN")
        current_date = form_data["date"]
        task_description = form_data["task_description"]
        activity_text = form_data["activity"]
        logger.passed(5, f"Generated Date: {current_date} | Task: '{task_description}' | Activity: '{activity_text}'")

        # Step 6: Select Date
        logger.step(6, "Select Date in Datepicker", f"Filling date input with {current_date}")
        team_tracker_page.select_date(current_date)
        logger.passed(6, f"Date selected: {current_date}")

        # Step 7: Select Shift Option
        logger.step(7, "Select Shift Option Dropdown", f"Selecting option: {form_data['option']}")
        team_tracker_page.select_option(form_data["option"])
        logger.passed(7, f"Option '{form_data['option']}' selected")

        # Step 8: Fill Task & Activity
        logger.step(8, "Fill Task and Activity Inputs", "Populating task and activity description fields")
        team_tracker_page.fill_task_and_activity(
            task_description=task_description,
            activity_text=activity_text,
        )
        logger.passed(8, "Task & Activity descriptions filled")

        # Step 9: Submit Form
        logger.step(9, "Submit Team Tracker Form", "Clicking Submit button with overlay handling")
        team_tracker_page.submit_form()
        logger.passed(9, "Submit button clicked successfully")

        # Step 10: Verify Toast
        logger.step(10, "Verify Success Toast Notification", "Checking for 'Data added to the spreadsheet'")
        team_tracker_page.verify_success_toast()
        logger.passed(10, "Toast notification confirmed: 'Data added to the spreadsheet'")

        # Step 11: Verify Data Stored in Spreadsheet Table
        logger.step(11, "Verify Stored Data in Spreadsheet Table", "Sorting by Date and validating new row entry")
        team_tracker_page.sort_table_by_date()
        team_tracker_page.verify_data_stored_in_table(
            task_description=task_description,
            activity_text=activity_text,
        )
        logger.passed(11, f"Table row verified: Task='{task_description}', Activity='{activity_text}'")

    except Exception as exc:
        failed_step = len(logger.steps_record) + 1
        logger.failed(failed_step, str(exc))
        raise
    finally:
        logger.finish_suite()


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
                print(f"[INFO] Report generated: {report_path}")
                import os
                if not os.environ.get("CI"):
                    webbrowser.open(report_path.as_uri())
            raise e
        finally:
            context.close()


if __name__ == "__main__":
    run_standalone()
