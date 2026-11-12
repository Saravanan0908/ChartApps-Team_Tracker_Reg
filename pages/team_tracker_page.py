"""Page Object representing Team Tracker form submission and spreadsheet data verification."""

from datetime import datetime
from typing import Optional
from playwright.sync_api import Locator, Page, expect
from constants.urls import AppUrls
from locators.team_tracker_locators import TeamTrackerLocators
from pages.base_page import BasePage


class TeamTrackerPage(BasePage):
    """Encapsulates Team Tracker form interactions and spreadsheet data table validations."""

    def __init__(self, page: Page):
        super().__init__(page)

    # --- Locators ---
    @property
    def close_modal_button(self) -> Locator:
        return self.page.get_by_role("button", name=TeamTrackerLocators.CLOSE_MODAL_BUTTON)

    @property
    def team_tracker_link(self) -> Locator:
        return self.page.get_by_role("link", name=TeamTrackerLocators.TEAM_TRACKER_LINK)

    @property
    def date_input(self) -> Locator:
        return self.page.get_by_role("textbox", name=TeamTrackerLocators.DATE_PICKER_INPUT)

    @property
    def dropdown_trigger(self) -> Locator:
        return self.page.get_by_placeholder(TeamTrackerLocators.DROPDOWN_PLACEHOLDER)

    @property
    def task_description_input(self) -> Locator:
        return self.page.get_by_role("textbox").nth(TeamTrackerLocators.TASK_DESCRIPTION_INPUT_INDEX)

    @property
    def activity_input(self) -> Locator:
        return self.page.get_by_role("textbox", name=TeamTrackerLocators.ACTIVITY_INPUT_NAME)

    @property
    def submit_button(self) -> Locator:
        return (
            self.page.get_by_role("button", name=TeamTrackerLocators.SUBMIT_BUTTON_EXACT_NAME)
            .or_(self.page.get_by_role("button", name=TeamTrackerLocators.SUBMIT_BUTTON_PATTERN))
            .or_(self.page.locator(TeamTrackerLocators.SUBMIT_BUTTON_CSS))
        )

    @property
    def success_toast(self) -> Locator:
        return self.page.get_by_text(TeamTrackerLocators.SUCCESS_TOAST_TEXT)

    @property
    def date_cell_header(self) -> Locator:
        return self.page.get_by_role("cell", name=TeamTrackerLocators.DATE_COLUMN_HEADER)

    @property
    def sort_column_icon(self) -> Locator:
        return self.page.locator(TeamTrackerLocators.SORT_COLUMN_ICON)

    # --- Actions ---
    def open_dashboard(self) -> None:
        """Navigate directly to the ChartApps dashboard and verify session."""
        self.navigate(AppUrls.DASHBOARD_URL)
        self.page.wait_for_load_state("domcontentloaded")
        
        # Check if redirected to auth screen (unauthenticated session)
        if "/auth" in self.page.url:
            raise RuntimeError(
                "Authentication required! The browser was redirected to '/dashboard/auth'. "
                "In GitHub Actions, you must add the 'AUTH_STORAGE_STATE' repository secret "
                "so the runner has the authenticated session. Locally, run 'tests/setup_auth.py'."
            )

    def close_modal_if_present(self) -> None:
        """Dismiss any announcement or popup modal if present."""
        try:
            if self.close_modal_button.first.is_visible(timeout=4000):
                self.close_modal_button.first.click()
        except Exception:
            pass

    def navigate_to_team_tracker(self) -> None:
        """Click on the Team Tracker navigation link."""
        self.team_tracker_link.first.click()

    def open_tracker_view(self, tracker_id: str = TeamTrackerLocators.DEFAULT_TRACKER_CARD_ID) -> None:
        """Open the specific tracker view by ID or fallback to the first view button."""
        card_locator = self.page.locator(f'[id="{tracker_id}"]')
        try:
            if card_locator.is_visible(timeout=3000):
                card_locator.get_by_role("button", name=TeamTrackerLocators.VIEW_BUTTON).click()
                return
        except Exception:
            pass
        # Fallback to any visible view button
        self.page.get_by_role("button", name=TeamTrackerLocators.VIEW_BUTTON).first.click()

    def select_date(self, date_str: Optional[str] = None) -> str:
        """Select current date in YYYY-MM-DD format using input click and fill."""
        selected_date = date_str or datetime.now().strftime("%Y-%m-%d")
        self.date_input.click()

        current_day_label = datetime.now().strftime("%B %d,")
        try:
            day_cell = self.page.get_by_label(current_day_label)
            if day_cell.is_visible(timeout=2000):
                day_cell.click()
        except Exception:
            pass

        self.date_input.fill(selected_date)
        self.page.keyboard.press("Escape")
        return selected_date

    def select_option(self, option_name: str = TeamTrackerLocators.DEFAULT_OPTION_NAME) -> None:
        """Select an option from the dropdown menu (e.g. FN)."""
        self.dropdown_trigger.click()
        self.page.get_by_role("option", name=option_name).click()

    def fill_task_and_activity(self, task_description: str, activity_text: str) -> None:
        """Fill Task / Activity fields incorporating current date and runtime."""
        self.task_description_input.click()
        self.task_description_input.fill(task_description)

        self.activity_input.click()
        self.activity_input.fill(activity_text)
        self.page.keyboard.press("Tab")

    def submit_form(self) -> None:
        """Click the Submit button with robust scroll and overlay-bypassing handling."""
        self.page.keyboard.press("Escape")

        btn = self.submit_button.first
        btn.scroll_into_view_if_needed()
        btn.wait_for(state="visible", timeout=10000)

        try:
            btn.click(timeout=5000)
        except Exception:
            print("[INFO] Retrying Submit button click with force=True...")
            btn.click(force=True)

    def verify_success_toast(self) -> None:
        """Verify toast notification confirming data added to the spreadsheet."""
        expect(self.success_toast.first).to_be_visible(timeout=10000)

    def sort_table_by_date(self) -> None:
        """Sort spreadsheet table by Date column to bring latest entries to top."""
        try:
            if self.date_cell_header.first.is_visible(timeout=5000):
                self.date_cell_header.first.click()
            if self.sort_column_icon.first.is_visible(timeout=3000):
                self.sort_column_icon.first.click()
        except Exception:
            pass

    def verify_data_stored_in_table(self, task_description: str, activity_text: str) -> None:
        """Verify that submitted task and activity data are stored and rendered in the spreadsheet."""
        task_locator = self.page.get_by_text(task_description).or_(self.page.locator(f'[title*="{task_description[:20]}"]'))
        activity_locator = self.page.get_by_text(activity_text)

        expect(task_locator.first).to_be_visible(timeout=10000)
        expect(activity_locator.first).to_be_visible(timeout=10000)
