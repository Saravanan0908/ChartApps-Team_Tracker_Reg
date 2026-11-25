"""ChartApps Complete Regression Suite: Existing & New App Workflows.

Supports tag-based and sequential scenario execution:
Scenario 1 (tag: existing_app): Existing App - Team Tracker Form Submission and Spreadsheet Data Storage.
Scenario 2 (tag: new_app):      New App - Creation, Google OAuth & Consent, Spreadsheet Selection,
                                Details Page, Blocks Configuration, Form Submission, End-User Verification, and Cleanup.
"""

import os
import sys
import time
import webbrowser
from pathlib import Path
from typing import Optional
import pytest
from playwright.sync_api import Page, Playwright, sync_playwright

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Suppress Playwright Inspector, recorder, and debug mode completely
import utils.suppress_debug

from pages.team_tracker_page import TeamTrackerPage
from pages.app_builder_page import AppBuilderPage
from testdata.team_tracker_data import TeamTrackerTestData
from testdata.new_app_data import NewAppTestData
from utils.browser_factory import launch_persistent_browser
from utils.config import HEADLESS, USER_DATA_DIR
from utils.step_logger import StepLogger


# ==============================================================================
# SCENARIO 1: EXISTING APP (TEAM TRACKER FORM & SPREADSHEET VERIFICATION)
# ==============================================================================

@pytest.mark.existing_app
def test_01_existing_app_team_tracker_regression(persistent_page: Page) -> None:
    """Scenario 1: Regression test on existing Team Tracker app."""
    logger = StepLogger(suite_name="Scenario 1: Existing App (Team Tracker)", total_steps=11)
    logger.start_suite()

    if isinstance(persistent_page, TeamTrackerPage):
        team_tracker_page = persistent_page
    else:
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
        if os.environ.get("CI") and ("Verify it’s you" in str(exc) or "Verify it's you" in str(exc) or "Google 2-Step" in str(exc)):
            pytest.skip(f"Google 2-Step Verification triggered on CI runner IP: {exc}")
        raise
    finally:
        logger.finish_suite()


# ==============================================================================
# SCENARIO 2: NEW APP CREATION & WORKFLOW VERIFICATION
# ==============================================================================

@pytest.mark.new_app
def test_02_new_app_creation_and_end_user_flow(
    persistent_page: Page,
    playwright: Optional[Playwright] = None,
) -> None:
    """Scenario 2: Create a new app, configure pages and blocks, submit form, verify as end-user, and cleanup."""
    logger = StepLogger(suite_name="Scenario 2: New App Creation & Workflow", total_steps=12)
    logger.start_suite()

    if isinstance(persistent_page, AppBuilderPage):
        builder_page = persistent_page
    else:
        builder_page = AppBuilderPage(persistent_page)

    data = NewAppTestData.get_new_app_payload()
    app_name = data["app_name"]
    app_slug = data["slug"]

    try:
        # Step 1: Open Dashboard
        logger.step(1, "Open Dashboard", "Navigating to ChartApps dashboard")
        builder_page.open_dashboard()
        logger.passed(1, "Dashboard reached")

        # Step 2: Initiate App Creation
        logger.step(2, "Initiate App Creation", f"Setting App Name: '{app_name}', Slug: '{app_slug}'")
        builder_page.initiate_create_app(app_name=app_name, app_slug=app_slug)
        logger.passed(2, "App name and subdomain filled")

        # Step 3: Google Account Connection & Consent
        logger.step(3, "Connect Google Account & Handle Consent", "Authenticating and accepting OAuth consent prompts (Continue / Next)")
        builder_page.connect_google_account_if_prompted()
        logger.passed(3, "Google Account authenticated and consent granted")

        # Step 4: Select Spreadsheet
        logger.step(4, "Select Google Spreadsheet", f"Selecting '{data['spreadsheet_name']}' via Google Picker")
        builder_page.select_google_spreadsheet(spreadsheet_name=data["spreadsheet_name"])
        logger.passed(4, "Spreadsheet selected from picker")

        # Step 5: Map Columns & Create Dashboard
        logger.step(5, "Map Columns and Create Dashboard", f"Mapping Sheet='{data['sheet_name']}', Name='{data['col_name']}', Email='{data['col_email']}'")
        builder_page.map_columns_and_create_dashboard(
            sheet=data["sheet_name"],
            name_col=data["col_name"],
            email_col=data["col_email"],
        )
        logger.passed(5, "Dashboard created and loaded in editor mode")

        # Step 6: Add Details Page
        logger.step(6, "Add 'About' Page", f"Creating new page '{data['page_name']}' linked to '{data['details_sheet']}'")
        builder_page.add_new_page(
            page_name=data["page_name"],
            slug=data["page_slug"],
            sheet=data["details_sheet"],
        )
        logger.passed(6, f"'{data['page_name']}' page added successfully")

        # Step 7: Configure Navigation Bar
        logger.step(7, "Configure Header Navigation", "Linking navigation bar to the newly created page")
        builder_page.configure_header_navigation()
        logger.passed(7, "Header navigation updated")

        # Step 8: Add Form Block & Submit in Editor Mode
        logger.step(8, "Add Form Block & Submit in Editor Mode", f"Adding Form Block on Home, configuring Date axis, and submitting record: '{data['editor_text'][:35]}...'")
        builder_page.add_form_block_to_home()
        submitted_editor_data = builder_page.submit_form_in_editor(
            date_str=data["editor_date"],
            text_val=data["editor_text"],
            datetime_str=data.get("editor_datetime"),
        )
        logger.passed(8, f"Form submitted in editor mode with Date='{submitted_editor_data['date']}', Text='{submitted_editor_data['text'][:30]}...'")

        # Step 9: Add Table Block to About Page
        logger.step(9, "Add Table Block to About Page", "Navigating to About page, adding Table block, and configuring teal styling")
        builder_page.add_table_block_to_about()
        logger.passed(9, "Table block added to About page")

        # Step 10: Verify Data in About Table
        logger.step(10, "Verify Stored Data in Table", "Asserting submitted Editor Mode record appears in About page table")
        builder_page.verify_table_contains_details(
            date_str=builder_page.last_submitted_editor_data["date"],
            expected_snippet=builder_page.last_submitted_editor_data["text"],
        )
        logger.passed(10, f"Submitted record confirmed in About page table (Date='{builder_page.last_submitted_editor_data['date']}')")

        # Step 11: Publish App & Set Privacy
        logger.step(11, "Publish App and Set Privacy", "Publishing app, making App Privacy switch active, and retrieving public URL")
        public_url = builder_page.publish_and_get_public_url()
        logger.passed(11, f"App published: {public_url}")

        # Step 12: End-User Submission & Cleanup
        logger.step(12, "End-User Verification & Cleanup", "Testing public app in fresh incognito context without cookies/caches, verifying Table, and deleting app")
        submitted_enduser_data = builder_page.submit_and_verify_as_end_user(
            public_url=public_url,
            date_str=data["enduser_date"],
            text_val=data["enduser_text"],
            playwright=playwright,
            browser=builder_page.page.context.browser,
        )
        builder_page.delete_app_and_cleanup(app_name=app_name)
        logger.passed(12, f"End-user flow verified with Date='{submitted_enduser_data['date']}' and app cleaned up successfully")

    except Exception as exc:
        failed_step = len(logger.steps_record) + 1
        logger.failed(failed_step, str(exc))
        if os.environ.get("CI") and ("Verify it’s you" in str(exc) or "Verify it's you" in str(exc) or "Google 2-Step" in str(exc)):
            pytest.skip(f"Google 2-Step Verification triggered on CI runner IP: {exc}")
        raise
    finally:
        logger.finish_suite()


# ==============================================================================
# STANDALONE EXECUTION RUNNER
# ==============================================================================

def run_standalone(target_scenario: str = "all") -> None:
    """Execute regression scenarios sequentially or by target filter in standalone mode."""
    target_scenario = (os.environ.get("SCENARIO") or target_scenario).lower()

    # Clear any debug/inspector flags to ensure uninterrupted execution
    utils.suppress_debug.suppress_playwright_inspector()

    print("=" * 75)
    print(f"Executing ChartApps Regression Suite (Scenario: {target_scenario.upper()} | Headless: {HEADLESS})")
    print("=" * 75)

    with sync_playwright() as playwright:
        context, page = launch_persistent_browser(
            playwright,
            user_data_dir=USER_DATA_DIR,
            headless=HEADLESS,
        )
        scenario_failures: list[tuple[str, Exception]] = []

        try:
            # 1. Execute Scenario 1: Existing App (if requested)
            if target_scenario in ("all", "existing", "existing_app"):
                print("\n" + "#" * 60)
                print(">>> SCENARIO 1: EXISTING APP (TEAM TRACKER) <<<")
                print("#" * 60)
                try:
                    test_01_existing_app_team_tracker_regression(page)
                    print("[SUCCESS] Scenario 1 Passed Successfully!\n")
                except Exception as sc1_err:
                    print(f"\n[ERROR] Scenario 1 Failed: {sc1_err}")
                    scenario_failures.append(("Scenario 1: Existing App (Team Tracker)", sc1_err))
                    reports_dir = Path("reports/screenshots")
                    reports_dir.mkdir(parents=True, exist_ok=True)
                    screenshot_path = reports_dir / f"failure_scenario1_{int(time.time())}.png"
                    try:
                        page.screenshot(path=str(screenshot_path))
                        print(f"[INFO] Failure screenshot captured for Scenario 1: {screenshot_path}")
                    except Exception:
                        pass
                    print("\n[INFO] As instructed: Error encountered in Existing App. Continuing directly to Scenario 2 (New App Creation)...\n")

            # 2. Execute Scenario 2: New App Creation & Workflow (if requested)
            if target_scenario in ("all", "new", "new_app"):
                print("\n" + "#" * 60)
                print(">>> SCENARIO 2: NEW APP CREATION & WORKFLOW <<<")
                print("#" * 60)
                try:
                    test_02_new_app_creation_and_end_user_flow(page, playwright=playwright)
                    print("[SUCCESS] Scenario 2 Passed Successfully!\n")
                except Exception as sc2_err:
                    print(f"\n[ERROR] Scenario 2 Failed: {sc2_err}")
                    scenario_failures.append(("Scenario 2: New App Creation & Workflow", sc2_err))
                    reports_dir = Path("reports/screenshots")
                    reports_dir.mkdir(parents=True, exist_ok=True)
                    screenshot_path = reports_dir / f"failure_scenario2_{int(time.time())}.png"
                    try:
                        page.screenshot(path=str(screenshot_path))
                        print(f"[INFO] Failure screenshot captured for Scenario 2: {screenshot_path}")
                    except Exception:
                        pass

            if scenario_failures:
                failed_names = ", ".join([name for name, _ in scenario_failures])
                raise AssertionError(f"Regression suite completed with failures: {failed_names}")

            print("\n" + "=" * 75)
            print("[COMPLETE] ALL REQUESTED REGRESSION SCENARIOS PASSED SUCCESSFULLY!")
            print("=" * 75)

            # Clean video files on pass
            try:
                from utils.video_helper import clean_passed_videos
                clean_passed_videos()
            except Exception:
                pass

        except Exception as e:
            print(f"\n[FAILURE] Regression test run failed: {e}")
            reports_dir = Path("reports/screenshots")
            reports_dir.mkdir(parents=True, exist_ok=True)
            screenshot_path = reports_dir / f"failure_regression_{int(time.time())}.png"
            try:
                page.screenshot(path=str(screenshot_path))
                print(f"[INFO] Failure screenshot captured: {screenshot_path}")
            except Exception:
                pass

            # Close context to flush video recording to disk and trim last 20 seconds
            try:
                context.close()
                from utils.video_helper import find_videos, trim_video_to_last_n_seconds
                videos = find_videos()
                if videos:
                    trimmed = trim_video_to_last_n_seconds(videos[0], max_seconds=20)
                    if trimmed:
                        print(f"[INFO] Processed last 20s failure video: {trimmed.name}")
            except Exception as vid_err:
                print(f"[WARNING] Could not process failure video: {vid_err}")

            allure_dir = Path("reports/allure-results").resolve()
            if allure_dir.exists():
                print(f"[INFO] Allure results recorded in: {allure_dir}")
            raise e
        finally:
            try:
                context.close()
            except Exception:
                pass


if __name__ == "__main__":
    cli_arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    run_standalone(cli_arg)
