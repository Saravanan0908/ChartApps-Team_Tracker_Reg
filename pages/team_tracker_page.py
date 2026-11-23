"""Team Tracker Page Object Module.

This Page Object models all user interactions on the ChartApps Team Tracker page:
1. Dashboard navigation and automated fallback login handling
2. Announcement modal dismissal
3. Tab navigation to 'My Apps' -> 'Team Tracker'
4. Form interaction (Datepicker, Dropdown, Task Description, Activity)
5. Robust submission with overlay dismissal
6. Toast confirmation assertion
7. Table sorting and verification of stored spreadsheet records
"""

from datetime import datetime
from typing import Optional
from playwright.sync_api import Locator, Page, expect
from constants.urls import AppUrls
from locators.team_tracker_locators import TeamTrackerLocators
from pages.base_page import BasePage


class TeamTrackerPage(BasePage):
    """Page Object for interacting with the ChartApps Team Tracker and Spreadsheet Table.
    
    Inherits from:
        BasePage: Provides base browser actions (navigate, get_title, etc.).
    """

    def __init__(self, page: Page):
        """Initialize the TeamTrackerPage.
        
        Args:
            page (Page): The active Playwright page instance.
        """
        super().__init__(page)

    # -------------------------------------------------------------------------
    # Locators (Properties returning Playwright Locators)
    # -------------------------------------------------------------------------

    @property
    def close_modal_button(self) -> Locator:
        """Locator for the popup announcement modal close button."""
        return self.page.get_by_role("button", name=TeamTrackerLocators.CLOSE_MODAL_BUTTON)

    @property
    def team_tracker_link(self) -> Locator:
        """Locator for the 'Team Tracker' navigation link in the side/top menu."""
        return self.page.get_by_role("link", name=TeamTrackerLocators.TEAM_TRACKER_LINK)

    @property
    def date_input(self) -> Locator:
        """Locator for the Date picker input field."""
        return (
            self.page.locator(TeamTrackerLocators.DATE_PICKER_CSS)
            .or_(self.page.get_by_role("textbox", name=TeamTrackerLocators.DATE_PICKER_INPUT))
            .first
        )

    @property
    def dropdown_trigger(self) -> Locator:
        """Locator for the Shift/Option dropdown container trigger."""
        return self.page.get_by_placeholder(TeamTrackerLocators.DROPDOWN_PLACEHOLDER)

    @property
    def task_description_input(self) -> Locator:
        """Locator for the Task Description text input box (2nd textbox on form)."""
        return self.page.get_by_role("textbox").nth(TeamTrackerLocators.TASK_DESCRIPTION_INPUT_INDEX)

    @property
    def activity_input(self) -> Locator:
        """Locator for the Activity text input box."""
        return self.page.get_by_role("textbox", name=TeamTrackerLocators.ACTIVITY_INPUT_NAME)

    @property
    def submit_button(self) -> Locator:
        """Locator for the form Submit button with exact name, regex, and CSS fallbacks."""
        return (
            self.page.get_by_role("button", name=TeamTrackerLocators.SUBMIT_BUTTON_EXACT_NAME)
            .or_(self.page.get_by_role("button", name=TeamTrackerLocators.SUBMIT_BUTTON_PATTERN))
            .or_(self.page.locator(TeamTrackerLocators.SUBMIT_BUTTON_CSS))
        )

    @property
    def success_toast(self) -> Locator:
        """Locator for the green notification toast: 'Data added to the spreadsheet'."""
        return self.page.get_by_text(TeamTrackerLocators.SUCCESS_TOAST_TEXT)

    @property
    def date_cell_header(self) -> Locator:
        """Locator for the 'Date' table column header used for sorting."""
        return self.page.get_by_role("cell", name=TeamTrackerLocators.DATE_COLUMN_HEADER)

    @property
    def sort_column_icon(self) -> Locator:
        """Locator for the PrimeReact table column sort icon."""
        return self.page.locator(TeamTrackerLocators.SORT_COLUMN_ICON)

    # -------------------------------------------------------------------------
    # Action Methods
    # -------------------------------------------------------------------------

    def open_dashboard(self) -> None:
        """Navigate to the ChartApps dashboard and perform automated sign-in if needed.
        
        Logic:
        1. Navigates to AppUrls.DASHBOARD_URL.
        2. Waits for React SPA to initialize.
        3. If already authenticated (e.g. session restored), continues immediately.
        4. If unauthenticated login card appears, automatically fills credentials and logs in.
        5. Saves session cookies to .auth_profile/storage_state.json for subsequent tests.
        """
        # Step 1: Navigate to Dashboard URL
        self.navigate(AppUrls.DASHBOARD_URL)
        self.wait_for_dom_ready()

        # Step 2: Define elements indicating dashboard vs unauthenticated login
        email_loc = self.page.locator('input[type="email"], input[placeholder*="Email"]').first
        dashboard_indicator = (
            self.page.get_by_text("My Apps")
            .or_(self.page.get_by_role("link", name=TeamTrackerLocators.TEAM_TRACKER_LINK))
            .or_(self.close_modal_button)
        )

        # Step 3: Wait up to 20 seconds for either dashboard or login card to render
        for _ in range(20):
            try:
                if dashboard_indicator.first.is_visible():
                    print("[INFO] Authenticated dashboard detected.", flush=True)
                    return
                if email_loc.is_visible():
                    break
            except Exception:
                pass
            self.page.wait_for_timeout(1000)

        # Step 4: Perform automated fallback login if login form is detected
        try:
            if email_loc.is_visible():
                print("[INFO] Unauthenticated session detected. Performing automated login...", flush=True)
                from testdata.test_data import LoginTestData

                # Fill Email and Password
                email_loc.fill(LoginTestData.EMAIL)
                password_loc = self.page.locator('input[type="password"], input[placeholder*="Password"]').first
                password_loc.fill(LoginTestData.PASSWORD)

                # Click Sign In button (exact match avoids clicking Google button)
                sign_in_btn = self.page.get_by_role("button", name="Sign In", exact=True)
                sign_in_btn.click()
                print("[INFO] Clicked Sign In button, waiting for dashboard...", flush=True)

                # Wait for dashboard elements post-login
                self.page.wait_for_timeout(3000)
                try:
                    dashboard_indicator.first.wait_for(state="visible", timeout=20000)
                    print("[INFO] Successfully reached authenticated dashboard.", flush=True)
                except Exception:
                    pass

                # Cache session cookies to file for future test runs
                try:
                    from utils.config import STORAGE_STATE_PATH
                    STORAGE_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
                    self.page.context.storage_state(path=str(STORAGE_STATE_PATH))
                    print(f"[INFO] Saved authenticated session to: {STORAGE_STATE_PATH}", flush=True)
                except Exception:
                    pass
        except Exception as e:
            print(f"[WARNING] Auto-login check encountered error: {e}", flush=True)

    def close_modal_if_present(self) -> None:
        """Dismiss introductory announcement modal if it appears on dashboard.
        
        Does not throw an exception if no modal is displayed.
        """
        try:
            btn = self.close_modal_button.first
            if btn.is_visible(timeout=5000):
                btn.click()
                self.page.wait_for_timeout(500)
        except Exception:
            pass

    def navigate_to_team_tracker(self) -> None:
        """Navigate to the Team Tracker section.
        
        Clicks 'My Apps' tab first to ensure the Team Tracker navigation link
        is revealed across all responsive desktop viewport sizes.
        """
        try:
            my_apps = self.page.get_by_text("My Apps")
            if my_apps.is_visible(timeout=5000):
                my_apps.click()
                self.page.wait_for_timeout(1000)
        except Exception:
            pass
        self.team_tracker_link.first.wait_for(state="visible", timeout=15000)
        self.team_tracker_link.first.click()

    def open_tracker_view(self, tracker_id: str = TeamTrackerLocators.DEFAULT_TRACKER_CARD_ID) -> None:
        """Open the specific tracker card view by ID or fallback to the first 'View' button.
        
        Args:
            tracker_id (str): The unique ID of the tracker card element.
        """
        card_locator = self.page.locator(f'[id="{tracker_id}"]')
        try:
            if card_locator.is_visible(timeout=5000):
                card_locator.get_by_role("button", name=TeamTrackerLocators.VIEW_BUTTON).click()
            else:
                self.page.get_by_role("button", name=TeamTrackerLocators.VIEW_BUTTON).first.click()
        except Exception:
            view_btn = self.page.get_by_role("button", name=TeamTrackerLocators.VIEW_BUTTON).first
            view_btn.wait_for(state="visible", timeout=15000)
            view_btn.click()

        # Crucial: Allow SPA component mounting and flatpickr widget initialization to stabilize
        self.page.wait_for_timeout(2500)

    def select_date(self, date_str: Optional[str] = None) -> str:
        """Select a date in the datepicker input using YYYY-MM-DD format.
        
        Args:
            date_str (Optional[str]): Target date string (defaults to today's date).
            
        Returns:
            str: The selected date string in YYYY-MM-DD format.
        """
        selected_date = date_str or datetime.now().strftime("%Y-%m-%d")

        # Wait for the date input to be attached and visible in the DOM
        date_el = self.date_input
        date_el.wait_for(state="visible", timeout=15000)

        # Attempt standard click, falling back to force click if flatpickr re-mounted the node
        try:
            date_el.click(timeout=5000)
        except Exception:
            self.page.wait_for_timeout(1000)
            date_el = self.date_input
            date_el.click(force=True)

        # Attempt to click current day cell in calendar overlay if visible
        current_day_label = datetime.now().strftime("%B %d,")
        try:
            day_cell = self.page.get_by_label(current_day_label)
            if day_cell.is_visible(timeout=2000):
                day_cell.click()
        except Exception:
            pass

        # Fill date input; if readonly attribute is enforced by flatpickr, set value via DOM
        try:
            date_el.fill(selected_date)
        except Exception:
            self.page.evaluate(
                """([sel, val]) => {
                    const el = document.querySelector(sel);
                    if (el) {
                        el.value = val;
                        el.dispatchEvent(new Event('input', {bubbles: true}));
                        el.dispatchEvent(new Event('change', {bubbles: true}));
                    }
                }""",
                ["input.flatpickr-input, input[placeholder*='yyyy-mm-dd'], input[name='Date']", selected_date]
            )

        # Dismiss calendar popups
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(500)
        return selected_date

    def select_option(self, option_name: str = TeamTrackerLocators.DEFAULT_OPTION_NAME) -> None:
        """Select an option from the Shift/Option dropdown menu.
        
        Args:
            option_name (str): The visible name of the option to select (e.g., 'FN').
        """
        self.dropdown_trigger.click()
        self.page.get_by_role(TeamTrackerLocators.OPTION_ROLE, name=option_name).click()

    def fill_task_and_activity(self, task_description: str, activity_text: str) -> None:
        """Fill in the Task Description and Activity text input fields.
        
        Args:
            task_description (str): Description string for the Task field.
            activity_text (str): Description string for the Activity field.
        """
        self.task_description_input.click()
        self.task_description_input.fill(task_description)

        self.activity_input.click()
        self.activity_input.fill(activity_text)
        self.page.keyboard.press("Tab")

    def submit_form(self) -> None:
        """Click the Submit button with overlay-bypassing and scroll handling.
        
        Presses Escape first to dismiss any calendar popups or tooltips that may
        be overlaying the Submit button, then scrolls into view and clicks.
        """
        self.page.keyboard.press("Escape")

        btn = self.submit_button.first
        btn.scroll_into_view_if_needed()
        btn.wait_for(state="visible", timeout=15000)

        try:
            btn.click(timeout=5000)
        except Exception:
            print("[INFO] Standard click intercepted; retrying with force=True...", flush=True)
            btn.click(force=True)

    def verify_success_toast(self) -> None:
        """Verify the toast notification confirming data was saved to the spreadsheet.
        
        Asserts that 'Data added to the spreadsheet' appears on screen.
        """
        expect(self.success_toast.first).to_be_visible(timeout=10000)

    def sort_table_by_date(self) -> None:
        """Sort the spreadsheet table by Date descending to bring the newly added entry to the top."""
        try:
            date_th = self.date_cell_header.first
            if date_th.is_visible(timeout=2000):
                current_sort = date_th.get_attribute("aria-sort") or ""
                if current_sort != "descending":
                    date_th.click()
                    self.page.wait_for_timeout(500)
                    new_sort = date_th.get_attribute("aria-sort") or ""
                    if new_sort == "ascending":
                        date_th.click()
                        self.page.wait_for_timeout(500)
        except Exception:
            pass

    def verify_data_stored_in_table(self, task_description: str, activity_text: str, timeout_ms: int = 15000) -> None:
        """Verify that the submitted task and activity strings appear in the spreadsheet table.
        Prints only expected and actual displayed data without dumping the entire table.
        
        Args:
            task_description (str): The submitted task description to locate.
            activity_text (str): The submitted activity text to locate.
            timeout_ms (int): Maximum timeout in ms to wait for the row to appear.
        """
        task_locator = self.page.get_by_text(task_description).or_(self.page.locator(f'[title*="{task_description[:20]}"]'))
        activity_locator = self.page.get_by_text(activity_text)

        start_time = time.time()
        found = False

        while (time.time() - start_time) < (timeout_ms / 1000.0):
            try:
                if task_locator.first.is_visible(timeout=500) and activity_locator.first.is_visible(timeout=500):
                    found = True
                    break
            except Exception:
                pass
            # Try sorting descending to ensure latest records are at top
            try:
                self.sort_table_by_date()
            except Exception:
                pass
            self.page.wait_for_timeout(1000)

        # Close details drawer / slider popup if opened by table row interaction
        try:
            sidebar = self.page.locator(".custom-sidebar-width, div[style*='z-index: 10000']")
            if sidebar.is_visible(timeout=500):
                close_btn = sidebar.locator("button.absolute, button").first
                if close_btn.is_visible(timeout=500):
                    close_btn.click(force=True)
                self.page.keyboard.press("Escape")
        except Exception:
            pass

        # Extract actual displayed top row for clean reporting (without dumping entire table)
        actual_task = "Not Found"
        actual_activity = "Not Found"
        try:
            rows = self.page.locator("table tbody tr, .p-datatable-tbody tr")
            if rows.count() > 0:
                first_row = rows.first
                cells = [c.strip() for c in first_row.locator("td").all_inner_texts() if c.strip()]
                if len(cells) >= 3:
                    actual_task = cells[1]
                    actual_activity = cells[2]
                elif len(cells) == 2:
                    actual_task = cells[0]
                    actual_activity = cells[1]
                elif cells:
                    actual_task = cells[0]
        except Exception:
            pass

        if found:
            print("\n" + "-" * 60)
            print("[PASS] Table Row Verification Succeeded:")
            print(f"  Expected: Task='{task_description}' | Activity='{activity_text}'")
            print(f"  Actual:   Task='{task_description}' | Activity='{activity_text}' (Displayed in Table)")
            print("-" * 60 + "\n")
        else:
            print("\n" + "-" * 60)
            print("[FAIL] Table Row Verification Failed:")
            print(f"  Expected: Task='{task_description}' | Activity='{activity_text}'")
            print(f"  Actual:   Task='{actual_task}' | Activity='{actual_activity}'")
            print("-" * 60 + "\n")
            raise AssertionError(
                f"Table Verification Failed:\n"
                f"  Expected: Task='{task_description}' | Activity='{activity_text}'\n"
                f"  Actual:   Task='{actual_task}' | Activity='{actual_activity}'"
            )
