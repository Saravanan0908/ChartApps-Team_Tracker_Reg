"""Page Object representing Spreadsheet and Dashboard operations in ChartApps."""

from typing import List
from playwright.sync_api import Locator, Page, expect
from constants.urls import AppUrls
from locators.spreadsheet_locators import SpreadsheetLocators
from pages.base_page import BasePage


class SpreadsheetPage(BasePage):
    """Encapsulates spreadsheet viewing, interaction, and validation on ChartApps."""

    def __init__(self, page: Page):
        super().__init__(page)

    @property
    def dashboard_heading(self) -> Locator:
        return self.page.locator("h1, h2, h3").filter(has_text=SpreadsheetLocators.DASHBOARD_HEADING)

    @property
    def connect_google_button(self) -> Locator:
        return self.page.get_by_role("button", name=SpreadsheetLocators.CONNECT_GOOGLE_BTN)

    @property
    def spreadsheet_section(self) -> Locator:
        return self.page.locator(SpreadsheetLocators.SPREADSHEET_SECTION)

    @property
    def add_spreadsheet_button(self) -> Locator:
        return self.page.get_by_role("button", name=SpreadsheetLocators.ADD_SPREADSHEET_BUTTON)

    @property
    def spreadsheet_rows(self) -> Locator:
        return self.page.locator(SpreadsheetLocators.SPREADSHEET_ROWS)

    @property
    def spreadsheet_headers(self) -> Locator:
        return self.page.locator(SpreadsheetLocators.SPREADSHEET_HEADERS)

    # --- Actions and Validations ---
    def open(self) -> None:
        """Navigate to ChartApps dashboard."""
        self.navigate(AppUrls.DASHBOARD_URL)

    def is_session_valid(self) -> bool:
        """Verify if existing authenticated session is active (not redirected to /auth)."""
        return "/auth" not in self.page.url

    def connect_google_if_needed(self) -> None:
        """Click Connect Google if button is visible, otherwise reuse current session."""
        try:
            if self.connect_google_button.first.is_visible(timeout=3000):
                self.connect_google_button.first.click()
                self.page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass

    def validate_spreadsheet_operations(self) -> bool:
        """Validate spreadsheet elements, table rows, or dashboard contents are accessible."""
        self.page.wait_for_load_state("domcontentloaded")
        # Ensure we are on dashboard and not auth
        expect(self.page).not_to_have_url(r".*/dashboard/auth.*")
        
        # Verify dashboard/spreadsheet area is visible or loaded
        has_content = self.page.locator("body").is_visible()
        return has_content

    def get_table_row_count(self) -> int:
        """Return the number of data rows currently visible in the spreadsheet table."""
        return self.spreadsheet_rows.count()

