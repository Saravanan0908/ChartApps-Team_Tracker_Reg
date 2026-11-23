"""App Builder Page Object for New App creation, page editing, blocks, publishing, and cleanup."""

import re
import time
from typing import Optional
from playwright.sync_api import BrowserContext, Page, expect

from locators.app_builder_locators import AppBuilderLocators
from pages.base_page import BasePage


class AppBuilderPage(BasePage):
    """Encapsulates all interactions with the ChartApps App Builder."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.dashboard_url = "https://chartapps.app/dashboard"

    def open_dashboard(self) -> None:
        """Navigate to ChartApps dashboard and ensure page is loaded."""
        self.page.goto(self.dashboard_url, wait_until="domcontentloaded")
        self.page.wait_for_timeout(2000)

    def initiate_create_app(self, app_name: str, app_slug: str) -> None:
        """Click 'Create App' button and enter app name and subdomain/slug."""
        create_btn = self.page.locator("button:has-text('Create App')").first
        create_btn.click()
        self.page.wait_for_timeout(1500)

        # First textbox is App Name
        name_input = self.page.get_by_role("textbox").first
        name_input.click()
        name_input.fill(app_name)

        # Second textbox is Subdomain / URL Slug
        slug_input = self.page.get_by_role("textbox").nth(1)
        slug_input.click()
        slug_input.fill(app_slug)

    def connect_google_account_if_prompted(self) -> None:
        """Connect Google Account and handle OAuth consent steps:
        1. Click 'Connect Your Google Account'
        2. page.get_by_role("link", name="chartapps chartapps.com@gmail").click()
        3. page.get_by_role("button", name="Continue").click()
        4. page.get_by_role("button", name="Continue").click()
        5. page.get_by_role("button", name="Next").click()
        """
        connect_btn = self.page.get_by_role("button", name="Connect Your Google Account")
        if not connect_btn.is_visible(timeout=4000):
            connect_btn = self.page.locator("button:has-text('Connect Your Google Account')").first

        active_page = self.page
        if connect_btn.is_visible(timeout=3000):
            try:
                with self.page.expect_popup(timeout=3000) as popup_info:
                    connect_btn.click()
                active_page = popup_info.value
            except Exception:
                connect_btn.click()
                active_page = self.page

        # Wait for Google page to settle (check popup or current tab)
        time.sleep(2)
        for p in self.page.context.pages:
            if not p.is_closed() and "google.com" in p.url:
                active_page = p
                break

        # Step 1: Select Google account link: "chartapps chartapps.com@gmail"
        try:
            account_link = active_page.get_by_role("link", name="chartapps chartapps.com@gmail")
            if not account_link.is_visible(timeout=4000):
                account_link = active_page.get_by_role("link", name=re.compile(r"chartapps.*@gmail", re.I))
            if not account_link.is_visible(timeout=2000):
                account_link = active_page.locator("text=chartapps.com@gmail.com, [data-email*='chartapps.com']").first
            if account_link.is_visible(timeout=3000):
                account_link.click()
                active_page.wait_for_timeout(2000)
        except Exception as e:
            print(f"[INFO] Google account selection step: {e}")

        # Step 2: First Continue button click
        try:
            cont1 = active_page.get_by_role("button", name="Continue")
            if not cont1.is_visible(timeout=4000):
                cont1 = active_page.locator("button:has-text('Continue'), [role='button']:has-text('Continue')").first
            if cont1.is_visible(timeout=3000):
                cont1.click()
                active_page.wait_for_timeout(2000)
        except Exception as e:
            print(f"[INFO] First Continue click step: {e}")

        # Step 3: Second Continue button click
        try:
            cont2 = active_page.get_by_role("button", name="Continue")
            if not cont2.is_visible(timeout=4000):
                cont2 = active_page.locator("button:has-text('Continue'), [role='button']:has-text('Continue')").first
            if cont2.is_visible(timeout=3000):
                cont2.click()
                active_page.wait_for_timeout(2000)
        except Exception as e:
            print(f"[INFO] Second Continue click step: {e}")

        # Step 4: Next button click
        try:
            next_btn = active_page.get_by_role("button", name="Next")
            if not next_btn.is_visible(timeout=4000):
                next_btn = active_page.locator("button:has-text('Next'), [role='button']:has-text('Next')").first
            if next_btn.is_visible(timeout=3000):
                next_btn.click()
                active_page.wait_for_timeout(2000)
        except Exception as e:
            print(f"[INFO] Next button click step: {e}")

        # Return focus to ChartApps page
        self.page.bring_to_front()
        self.page.wait_for_timeout(2500)

    def select_google_spreadsheet(self, spreadsheet_name: str = "Regression Testing Automation") -> None:
        """Open Google Picker and select spreadsheet."""
        select_sheet_btn = self.page.locator("button:has-text('Select Your Spreadsheet')").first
        select_sheet_btn.click()
        self.page.wait_for_timeout(3000)

        # Find the Google Picker iframe dynamically
        picker_frame = None
        for frame in self.page.frames:
            if "picker" in frame.url or "google.com" in frame.url:
                picker_frame = frame
                break

        if picker_frame:
            picker_frame.locator(f"[role='option']:has-text('{spreadsheet_name}')").first.click()
            picker_frame.locator("button:has-text('Select')").first.click()
        else:
            picker_locator = self.page.frame_locator(AppBuilderLocators.SPREADSHEET_IFRAME_CSS).first
            picker_locator.locator(f"[role='option']:has-text('{spreadsheet_name}')").first.click()
            picker_locator.locator("button:has-text('Select')").first.click()

        self.page.wait_for_timeout(2500)

    def map_columns_and_create_dashboard(
        self,
        sheet: str = "User",
        name_col: str = "Name ",
        email_col: str = "Email",
    ) -> str:
        """Select sheet and column mapping, then click 'Create Dashboard'."""
        combos = self.page.get_by_role("combobox")
        combos.first.select_option(sheet)
        combos.nth(1).select_option(name_col)
        combos.nth(2).select_option(email_col)

        self.page.get_by_role("button", name="Create Dashboard").click()
        self.page.wait_for_timeout(5000)
        return self.page.url

    def add_new_page(
        self,
        page_name: str = "About",
        slug: str = "about",
        sheet: str = "Regression Submition",
    ) -> None:
        """Add a new page in editor mode with designated details sheet."""
        pages_item = self.page.locator("li:has-text('Pages'), [name='Pages']").first
        pages_item.click()
        self.page.wait_for_timeout(1000)

        # Click Add
        self.page.get_by_role("button", name="Add").click()
        self.page.wait_for_timeout(1000)

        # Fill Page Name and URL slug
        page_name_input = self.page.get_by_role("textbox", name=AppBuilderLocators.PAGE_NAME_INPUT)
        page_name_input.click()
        page_name_input.fill(page_name)

        slug_input = self.page.get_by_role("textbox", name=AppBuilderLocators.URL_SLUG_INPUT)
        slug_input.click()
        slug_input.fill(slug)

        # Select sheet for details page
        sheet_selector = self.page.get_by_label("Select sheet for details page")
        sheet_selector.select_option(sheet)

        # Save and close
        self.page.get_by_role("button", name="Save").click()
        self.page.wait_for_timeout(1000)
        self.page.get_by_role("button", name="Close").click()
        self.page.wait_for_timeout(1000)

    def configure_header_navigation(self) -> None:
        """Configure Header navigation bar to link to the new page."""
        self.page.get_by_text("Header").click()
        self.page.wait_for_timeout(1000)
        self.page.get_by_role("tab", name=AppBuilderLocators.NAVIGATION_BAR_TAB).click()
        self.page.wait_for_timeout(1000)

        # Select the newly added page in dropdown
        combos = self.page.get_by_role("combobox")
        if combos.count() >= 4:
            target_combo = combos.nth(3)
            options = target_combo.locator("option").all()
            if len(options) > 1:
                target_combo.select_option(index=len(options) - 1)
        self.page.get_by_role("button", name="Save").click()
        self.page.wait_for_timeout(1500)

    def add_blocks_to_editor(self) -> None:
        """Add and configure Form and Table blocks across Home and About pages."""
        # 1. Home Page Form Block
        self.page.get_by_role("link", name="Home").click()
        self.page.wait_for_timeout(1500)
        new_block = self.page.locator("li:has-text('New Block')").first
        new_block.click()
        self.page.wait_for_timeout(1000)

        # Select form block from grid
        self.page.locator(".category > .block-grid > div:nth-child(3) > .hover-overlay").click()
        self.page.wait_for_timeout(1000)
        self.page.get_by_role("tab", name=AppBuilderLocators.AXES_TAB).click()
        self.page.wait_for_timeout(1000)
        self.page.get_by_role("region", name=AppBuilderLocators.AXES_TAB).get_by_role("button").click()
        self.page.wait_for_timeout(500)

        # Date / Datetime configuration
        date_btn = self.page.get_by_role("button", name="Date")
        if date_btn.is_visible(timeout=2000):
            date_btn.click()
        axes_region = self.page.get_by_role("region", name=AppBuilderLocators.AXES_TAB)
        type_select = axes_region.locator("#type")
        if type_select.is_visible(timeout=2000):
            type_select.select_option("datetime-local")
        self.page.get_by_role("button", name="Save").click()
        self.page.wait_for_timeout(1500)

        # 2. About Page Table Block
        self.page.get_by_role("link", name="About").click()
        self.page.wait_for_timeout(1500)
        new_block = self.page.locator("li:has-text('New Block')").first
        new_block.click()
        self.page.wait_for_timeout(1000)

        # Select table block from grid
        self.page.locator(".category > .block-grid > div:nth-child(2) > .hover-overlay").click()
        self.page.wait_for_timeout(1000)
        axes_btn = self.page.get_by_role("region", name=AppBuilderLocators.AXES_TAB).get_by_role("button").filter(has_text=re.compile(r"^$"))
        if axes_btn.is_visible(timeout=2000):
            axes_btn.click()
        ring_btn = self.page.locator(".rounded-full.hover\\:ring-4.ring-teal-500").first
        if ring_btn.is_visible(timeout=2000):
            ring_btn.click()
        self.page.get_by_role("button", name="Save").click()
        self.page.wait_for_timeout(1500)

    def submit_form_in_editor(self, datetime_str: str, date_str: str, text_val: str) -> None:
        """Submit form data in editor mode."""
        self.page.get_by_role("link", name="Home").click()
        self.page.wait_for_timeout(2000)

        # Fill datetime
        dt_input = self.page.get_by_role("textbox", name="yyyy-mm-dd HH:MM")
        if dt_input.is_visible(timeout=3000):
            dt_input.fill(datetime_str)

        # Fill date
        d_input = self.page.get_by_role("textbox", name="yyyy-mm-dd")
        if d_input.is_visible(timeout=3000):
            d_input.fill(date_str)

        # Fill text
        txt_input = self.page.get_by_role("textbox", name="Type here..")
        if txt_input.is_visible(timeout=3000):
            txt_input.fill(text_val)

        # Submit
        self.page.get_by_role("button", name=AppBuilderLocators.SUBMIT_BUTTON).click()
        self.page.wait_for_timeout(3000)

    def verify_record_in_about_table(self, expected_snippet: str) -> bool:
        """Verify submitted record appears in the About page table."""
        self.page.get_by_role("link", name="About").click()
        self.page.wait_for_timeout(3000)

        table = self.page.get_by_role("table")
        expect(table).to_be_visible(timeout=10000)
        match_element = table.get_by_text(expected_snippet)
        expect(match_element).to_be_visible(timeout=10000)
        return True

    def publish_and_get_public_url(self) -> str:
        """Publish app and configure public privacy settings, returning public URL."""
        self.page.get_by_role("button", name="Publish").click()
        self.page.wait_for_timeout(1000)
        self.page.get_by_role("button", name="Privacy Settings").click()
        self.page.wait_for_timeout(1000)

        # Check App privacy
        privacy_checkbox = self.page.get_by_role("checkbox", name="App privacy")
        if privacy_checkbox.is_visible(timeout=2000) and not privacy_checkbox.is_checked():
            privacy_checkbox.check()

        self.page.get_by_role("button", name="Save").click()
        self.page.wait_for_timeout(1500)

        # Get Public URL from input or current origin
        public_url_input = self.page.get_by_role("textbox", name="Enter public URL")
        if public_url_input.is_visible(timeout=3000):
            url_val = public_url_input.input_value()
            if url_val:
                return url_val

        curr = self.page.url
        base_url = curr.split("?")[0].rstrip("/")
        return base_url

    def submit_and_verify_as_end_user(
        self,
        public_url: str,
        date_str: str,
        text_val: str,
        context: BrowserContext,
    ) -> None:
        """Open a new tab/session as an end-user, submit the form, and verify."""
        user_page = context.new_page()
        try:
            user_page.goto(public_url, wait_until="domcontentloaded")
            user_page.wait_for_timeout(3000)

            # Fill date
            d_input = user_page.get_by_role("textbox", name="yyyy-mm-dd")
            if d_input.is_visible(timeout=5000):
                d_input.fill(date_str)

            # Fill text
            txt_input = user_page.get_by_role("textbox", name="Type here..")
            if txt_input.is_visible(timeout=5000):
                txt_input.fill(text_val)

            # Submit
            user_page.get_by_role("button", name=AppBuilderLocators.SUBMIT_BUTTON).click()
            user_page.wait_for_timeout(3000)

            # Navigate to About and verify
            user_page.get_by_role("link", name="About").click()
            user_page.wait_for_timeout(3000)

            table = user_page.get_by_role("table")
            expect(table).to_be_visible(timeout=10000)
            record = table.get_by_text(text_val[:25])
            expect(record).to_be_visible(timeout=10000)
        finally:
            user_page.close()

    def delete_app_and_cleanup(self, app_name: str) -> None:
        """Delete the created app from ChartApps and confirm dialog."""
        del_btn = self.page.get_by_role("button", name="Delete App")
        if not del_btn.is_visible(timeout=3000):
            sidebar_icon = self.page.locator("li:has-text('Settings'), li:nth-child(5) .sidebar-item-content").first
            if sidebar_icon.is_visible(timeout=3000):
                sidebar_icon.click()
                self.page.wait_for_timeout(1000)

        del_btn = self.page.get_by_role("button", name="Delete App")
        if del_btn.is_visible(timeout=3000):
            self.page.once("dialog", lambda dialog: dialog.accept())
            del_btn.click()
            self.page.wait_for_timeout(3000)
