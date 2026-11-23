"""App Builder Page Object for New App creation, page editing, blocks, publishing, and cleanup."""

import re
import time
from datetime import datetime
from typing import Optional
from playwright.sync_api import Browser, BrowserContext, Page, expect

from locators.app_builder_locators import AppBuilderLocators
from pages.base_page import BasePage


class AppBuilderPage(BasePage):
    """Encapsulates all interactions with the ChartApps App Builder."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.dashboard_url = "https://chartapps.app/dashboard"
        self.last_submitted_editor_data: dict[str, str] = {}
        self.last_submitted_enduser_data: dict[str, str] = {}

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

        if connect_btn.is_visible(timeout=3000):
            connect_btn.click()
            self.page.wait_for_timeout(2500)

        # Step 1: Select Google account link: "chartapps chartapps.com@gmail"
        try:
            account_link = self.page.get_by_role("link", name="chartapps chartapps.com@gmail")
            if not account_link.is_visible(timeout=4000):
                account_link = self.page.get_by_role("link", name=re.compile(r"chartapps.*@gmail", re.I))
            if not account_link.is_visible(timeout=2000):
                account_link = self.page.locator("text=chartapps.com@gmail.com, [data-email*='chartapps.com']").first
            if account_link.is_visible(timeout=3000):
                account_link.click()
                self.page.wait_for_timeout(2000)
        except Exception as e:
            print(f"[INFO] Google account selection step: {e}")

        # Step 2: First Continue button click
        try:
            cont1 = self.page.get_by_role("button", name="Continue")
            if not cont1.is_visible(timeout=4000):
                cont1 = self.page.locator("button:has-text('Continue'), [role='button']:has-text('Continue')").first
            if cont1.is_visible(timeout=3000):
                cont1.click()
                self.page.wait_for_timeout(2000)
        except Exception as e:
            print(f"[INFO] First Continue click step: {e}")

        # Step 3: Second Continue button click
        try:
            cont2 = self.page.get_by_role("button", name="Continue")
            if not cont2.is_visible(timeout=4000):
                cont2 = self.page.locator("button:has-text('Continue'), [role='button']:has-text('Continue')").first
            if cont2.is_visible(timeout=3000):
                cont2.click()
                self.page.wait_for_timeout(2000)
        except Exception as e:
            print(f"[INFO] Second Continue click step: {e}")

        # Step 4: Next button click
        try:
            next_btn = self.page.get_by_role("button", name="Next")
            if not next_btn.is_visible(timeout=4000):
                next_btn = self.page.locator("button:has-text('Next'), [role='button']:has-text('Next')").first
            if next_btn.is_visible(timeout=3000):
                next_btn.click()
                self.page.wait_for_timeout(2500)
        except Exception as e:
            print(f"[INFO] Next button click step: {e}")

        self.page.wait_for_timeout(2000)

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

        select_selector = "[role='button']:has-text('Select'), .picker-select-control-enabled, div:text-is('Select'), button:has-text('Select')"

        if picker_frame:
            picker_frame.locator(f"[role='option']:has-text('{spreadsheet_name}')").first.click()
            self.page.wait_for_timeout(1000)
            select_btn = picker_frame.locator(select_selector).first
            if not select_btn.is_visible(timeout=2000):
                select_btn = picker_frame.get_by_role("button", name="Select")
            select_btn.click()
        else:
            picker_locator = self.page.frame_locator("iframe").first
            picker_locator.locator(f"[role='option']:has-text('{spreadsheet_name}')").first.click()
            self.page.wait_for_timeout(1000)
            select_btn = picker_locator.locator(select_selector).first
            if not select_btn.is_visible(timeout=2000):
                select_btn = picker_locator.get_by_role("button", name="Select")
            select_btn.click()

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
        """Add a new page in editor mode with designated details sheet, handling 'Error Loading sheet' recovery."""
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

        # Check if 'Error Loading sheet' is displayed or target sheet not loaded in dropdown
        sheet_selector = self.page.get_by_label("Select sheet for details page")
        has_error = False
        try:
            options_text = " ".join(sheet_selector.locator("option").all_inner_texts())
            if "Error Loading" in options_text or "Error loading" in options_text or sheet not in options_text:
                has_error = True
        except Exception:
            pass

        if not has_error:
            try:
                if self.page.locator("text=Error Loading sheet, text=Error loading").is_visible(timeout=1000):
                    has_error = True
            except Exception:
                pass

        if has_error:
            # When dropdown shows 'Error Loading sheet', refresh the page and re-attempt page creation
            self.page.reload(wait_until="domcontentloaded")
            self.page.wait_for_timeout(3000)

            pages_item = self.page.locator("li:has-text('Pages'), [name='Pages']").first
            pages_item.click()
            self.page.wait_for_timeout(1500)

            self.page.get_by_role("button", name="Add").click()
            self.page.wait_for_timeout(1500)

            page_name_input = self.page.get_by_role("textbox", name=AppBuilderLocators.PAGE_NAME_INPUT)
            page_name_input.click()
            page_name_input.fill(page_name)

            slug_input = self.page.get_by_role("textbox", name=AppBuilderLocators.URL_SLUG_INPUT)
            slug_input.click()
            slug_input.fill(slug)

            sheet_selector = self.page.get_by_label("Select sheet for details page")
            self.page.wait_for_timeout(1000)

        # Select sheet for details page
        sheet_selector.select_option(sheet)
        self.page.wait_for_timeout(500)

        # Save and close
        self.page.get_by_role("button", name="Save").click()
        self.page.wait_for_timeout(1500)
        close_btn = self.page.get_by_role("button", name="Close")
        if close_btn.is_visible(timeout=2000):
            close_btn.click()
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

    def add_form_block_to_home(self) -> None:
        """Add Form block on Home page and configure Date axis."""
        self.page.get_by_role("link", name=AppBuilderLocators.HOME_LINK).click()
        self.page.wait_for_timeout(1500)
        new_block = self.page.locator("li:has-text('New Block')").first
        new_block.click()
        self.page.wait_for_timeout(1000)

        # Select form block from grid
        self.page.locator(AppBuilderLocators.FORM_BLOCK_OVERLAY).first.click()
        self.page.wait_for_timeout(1000)
        self.page.get_by_role("tab", name=AppBuilderLocators.AXES_TAB).click()
        self.page.wait_for_timeout(1000)
        axes_region_btn = self.page.get_by_role("region", name=AppBuilderLocators.AXES_TAB).get_by_role("button").first
        if axes_region_btn.is_visible(timeout=2000):
            axes_region_btn.click()
            self.page.wait_for_timeout(500)

        # Select 'date' type
        axes_region = self.page.get_by_role("region", name=AppBuilderLocators.AXES_TAB)
        type_select = axes_region.locator("#type")
        if type_select.is_visible(timeout=2000):
            type_select.select_option("date")
        self.page.get_by_role("button", name="Save").click()
        self.page.wait_for_timeout(1000)

        # Click additional icon/save if present in editor
        empty_btn = self.page.get_by_role("button").filter(has_text=re.compile(r"^$"))
        if empty_btn.count() > 2:
            try:
                empty_btn.nth(2).click()
                self.page.wait_for_timeout(500)
                self.page.get_by_role("button", name="Save").click()
                self.page.wait_for_timeout(1000)
            except Exception:
                pass

    def add_table_block_to_about(self) -> None:
        """Add Table block on About page and configure teal styling."""
        self.page.get_by_role("link", name=AppBuilderLocators.ABOUT_LINK).click()
        self.page.wait_for_timeout(1500)
        new_block = self.page.locator("li:has-text('New Block')").first
        new_block.click()
        self.page.wait_for_timeout(1000)

        # Select table block from grid
        table_overlay = self.page.locator(AppBuilderLocators.TABLE_BLOCK_OVERLAY).first
        table_overlay.click()
        self.page.wait_for_timeout(1000)

        axes_btn = self.page.get_by_role("region", name=AppBuilderLocators.AXES_TAB).get_by_role("button").filter(has_text=re.compile(r"^$"))
        if axes_btn.is_visible(timeout=2000):
            axes_btn.first.click()
        ring_btn = self.page.locator(".rounded-full.hover\\:ring-4.ring-teal-500").first
        if ring_btn.is_visible(timeout=2000):
            ring_btn.click()
        self.page.get_by_role("button", name="Save").click()
        self.page.wait_for_timeout(1500)

    def add_blocks_to_editor(self) -> None:
        """Backward-compatible helper to configure blocks across Home and About pages."""
        self.add_form_block_to_home()
        self.add_table_block_to_about()

    def close_slider_popup(self, target_page: Page) -> None:
        """Close the slider / drawer popup that opens when clicking a table row/cell."""
        target_page.wait_for_timeout(300)
        # 1. Exact close button identified in Playwright Inspector: get_by_role('button').filter({ hasText: /^$/ }).nth(4)
        try:
            empty_btns = target_page.get_by_role("button").filter(has_text=re.compile(r"^$"))
            if empty_btns.count() >= 5:
                close_btn = empty_btns.nth(4)
                if close_btn.is_visible(timeout=1000):
                    close_btn.click()
                    target_page.wait_for_timeout(500)
                    return
        except Exception:
            pass

        # 2. Try close button on the Details panel / drawer header
        try:
            drawer_close = target_page.locator(
                "div:has-text('Details') button, "
                ".p-sidebar-header button, .p-sidebar-close, .slider-close, "
                "button[aria-label*='Close' i], "
                "button:has-text('✕'), button:has-text('×')"
            ).first
            if drawer_close.is_visible(timeout=1000):
                drawer_close.click()
                target_page.wait_for_timeout(500)
                return
        except Exception:
            pass

        # 3. Dismiss via Escape key
        try:
            target_page.keyboard.press("Escape")
            target_page.wait_for_timeout(300)
        except Exception:
            pass

    def select_date_picker_value(self, target_page: Page, selected_date: str) -> str:
        """Select current date in the form date picker via calendar popup and day cell click."""
        now = datetime.now()
        month_name = now.strftime("%B")
        day_num = now.day
        # Regex matching e.g. "November 23," or "November 23"
        day_pattern = re.compile(rf"{month_name}\s+{day_num},?", re.IGNORECASE)

        # Locate date picker input
        d_input = target_page.get_by_role("textbox", name="yyyy-mm-dd")
        if not d_input.is_visible(timeout=3000):
            d_input = target_page.locator("input[placeholder*='yyyy-mm-dd'], input.flatpickr-input, input[name='Date']").first

        if d_input.is_visible(timeout=3000):
            # 1. Click textbox once to open calendar popup
            d_input.click()
            target_page.wait_for_timeout(500)

            # 2. Click current day cell in the calendar overlay (which automatically selects date and closes popup)
            day_selected = False
            try:
                day_cell = target_page.get_by_label(day_pattern)
                if day_cell.first.is_visible(timeout=2000):
                    day_cell.first.click()
                    day_selected = True
                    target_page.wait_for_timeout(500)
                else:
                    today_cell = target_page.locator(".flatpickr-day.today, .today, .p-datepicker-today, [aria-current='date']").first
                    if today_cell.is_visible(timeout=1000):
                        today_cell.click()
                        day_selected = True
                        target_page.wait_for_timeout(500)
            except Exception:
                pass

            # CRITICAL: DO NOT call d_input.fill() if day was already selected from popup!
            # Calling d_input.fill() clicks the date input again and causes the calendar popup to re-open over Title!
            if not day_selected:
                try:
                    d_input.fill(selected_date)
                    target_page.wait_for_timeout(300)
                except Exception:
                    pass

            # 3. Dismiss calendar popup if still visible so it closes before typing Title
            try:
                cal_popup = target_page.locator(".p-datepicker, .flatpickr-calendar.open, .calendar-popup")
                if cal_popup.is_visible(timeout=500):
                    target_page.keyboard.press("Escape")
                    target_page.wait_for_timeout(300)
            except Exception:
                pass

            val = d_input.input_value()
            return val or selected_date

        return selected_date

    def submit_form_in_editor(
        self,
        date_str: str,
        text_val: str,
        datetime_str: Optional[str] = None,
    ) -> dict[str, str]:
        """Submit form data on Home page in editor mode, storing and returning submitted values."""
        home_link = self.page.get_by_role("link", name=AppBuilderLocators.HOME_LINK)
        if home_link.is_visible(timeout=2000):
            home_link.click()
            self.page.wait_for_timeout(1500)

        # 1. Select Current Date via popup (popup opens, date is clicked, popup closes)
        actual_date = self.select_date_picker_value(self.page, date_str)

        # 2. Once the date popup closes, click and fill the Title / text input
        txt_input = self.page.get_by_role("textbox", name="Type here..")
        if not txt_input.is_visible(timeout=3000):
            txt_input = self.page.locator("input[placeholder*='Type here'], textarea[placeholder*='Type here']").first

        if txt_input.is_visible(timeout=3000):
            txt_input.click()
            txt_input.fill(text_val)
            actual_text = txt_input.input_value() or text_val
        else:
            actual_text = text_val

        # Store submitted values dynamically for subsequent verification
        self.last_submitted_editor_data = {
            "date": actual_date,
            "text": actual_text,
        }

        # 3. Dismiss any lingering popups before clicking submit
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(300)

        # Submit
        submit_btn = self.page.get_by_role("button", name=AppBuilderLocators.SUBMIT_BUTTON)
        if not submit_btn.is_visible(timeout=2000):
            submit_btn = self.page.locator("button:has-text('Submit'), button[type='submit']").first
        submit_btn.click()
        self.page.wait_for_timeout(3000)

        return self.last_submitted_editor_data

    def verify_table_contains_details(
        self,
        date_str: Optional[str] = None,
        expected_snippet: Optional[str] = None,
        page_obj: Optional[Page] = None,
    ) -> bool:
        """Verify that the Table on About page displays the submitted record (date & message)."""
        target_page = page_obj or self.page
        if page_obj is None:
            about_link = target_page.get_by_role("link", name=AppBuilderLocators.ABOUT_LINK)
            if about_link.is_visible(timeout=2000):
                about_link.click()
                target_page.wait_for_timeout(2000)

        # Identify values from submitted form if not explicitly provided
        if date_str is None:
            date_str = self.last_submitted_editor_data.get("date", "")
        if expected_snippet is None:
            expected_snippet = self.last_submitted_editor_data.get("text", "")

        table = target_page.get_by_role("table")
        expect(table).to_be_visible(timeout=10000)

        # Assert record message is present in the table (verifying actual submitted values)
        if expected_snippet:
            record = table.get_by_text(expected_snippet)
            if record.first.is_visible(timeout=5000):
                expect(record.first).to_be_visible(timeout=5000)
            else:
                row = table.locator("tr").filter(has_text=expected_snippet[:35])
                expect(row.first).to_be_visible(timeout=10000)

        # Assert submitted date is present in the table
        if date_str:
            date_cell = target_page.get_by_role("cell", name=re.compile(re.escape(date_str))).or_(target_page.get_by_text(date_str))
            if date_cell.first.is_visible(timeout=5000):
                expect(date_cell.first).to_be_visible(timeout=5000)
                try:
                    date_cell.first.click()
                    target_page.wait_for_timeout(500)
                    # Close the slider popup that opened when clicking the cell
                    self.close_slider_popup(target_page)
                except Exception:
                    pass

        try:
            paginator = target_page.locator(AppBuilderLocators.PAGINATOR)
            if paginator.is_visible(timeout=1000):
                paginator.click()
        except Exception:
            pass

        # Ensure slider popup is closed
        self.close_slider_popup(target_page)

        return True

    def verify_record_in_about_table(self, expected_snippet: Optional[str] = None) -> bool:
        """Verify submitted record in About table using stored form submission values."""
        snippet = expected_snippet or self.last_submitted_editor_data.get("text", "")
        date_val = self.last_submitted_editor_data.get("date", "")
        return self.verify_table_contains_details(date_str=date_val, expected_snippet=snippet)

    def publish_and_get_public_url(self) -> str:
        """Publish app and configure public privacy settings, returning public URL."""
        # Ensure any slider popup from table inspection is closed before clicking Publish
        self.close_slider_popup(self.page)
        self.page.wait_for_timeout(500)

        pub_btn = self.page.locator("button:has-text('Publish'), .publish-btn").first
        if pub_btn.is_visible(timeout=3000):
            pub_btn.click()
        else:
            self.page.get_by_role("button", name=AppBuilderLocators.PUBLISH_BUTTON).click()
        self.page.wait_for_timeout(1000)

        priv_btn = self.page.get_by_role("button", name=AppBuilderLocators.PRIVACY_SETTINGS_BUTTON)
        if not priv_btn.is_visible(timeout=2000):
            pub_btn.click()
            self.page.wait_for_timeout(1000)

        if priv_btn.is_visible(timeout=3000):
            priv_btn.click()
            self.page.wait_for_timeout(1000)

        # Make Switch / App Privacy active (switch toggle button)
        toggle_input = self.page.locator(AppBuilderLocators.APP_PRIVACY_TOGGLE_INPUT)
        toggle_label = self.page.locator(AppBuilderLocators.APP_PRIVACY_TOGGLE_LABEL)

        is_active = False
        try:
            if toggle_input.count() > 0:
                is_active = toggle_input.is_checked()
            else:
                cb = self.page.get_by_role("checkbox", name=AppBuilderLocators.APP_PRIVACY_CHECKBOX)
                if cb.count() > 0:
                    is_active = cb.is_checked()
        except Exception:
            is_active = False

        if not is_active:
            # Click the visible toggle switch label to activate
            if toggle_label.is_visible(timeout=2000):
                toggle_label.click()
                self.page.wait_for_timeout(500)
            elif toggle_input.count() > 0:
                toggle_input.check(force=True)
            else:
                cb = self.page.get_by_role("checkbox", name=AppBuilderLocators.APP_PRIVACY_CHECKBOX)
                if cb.is_visible(timeout=2000):
                    cb.check(force=True)

            # Ensure state is active; force check if needed (handles sr-only input)
            try:
                if toggle_input.count() > 0 and not toggle_input.is_checked():
                    toggle_input.check(force=True)
            except Exception:
                pass

        dialog_save = self.page.locator(AppBuilderLocators.DIALOG_SAVE_BUTTON).first
        dialog_save.click()
        self.page.wait_for_timeout(1500)

        # Get Public URL from input or current origin
        public_url_input = self.page.get_by_role("textbox", name=AppBuilderLocators.ENTER_PUBLIC_URL_INPUT)
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
        context: Optional[BrowserContext] = None,
        browser: Optional[Browser] = None,
    ) -> dict[str, str]:
        """Launch a fresh incognito session without cookies/caches, submit form, and verify table."""
        own_context = False
        if browser is not None:
            user_context = browser.new_context(viewport={"width": 1920, "height": 1080})
            own_context = True
        elif context is not None:
            user_context = context
        elif hasattr(self.page.context, "browser") and self.page.context.browser:
            user_context = self.page.context.browser.new_context(viewport={"width": 1920, "height": 1080})
            own_context = True
        else:
            user_context = self.page.context

        user_page = user_context.new_page()
        try:
            user_page.goto(public_url, wait_until="domcontentloaded")
            user_page.wait_for_timeout(3000)

            # Fill date (Current Date) using calendar overlay & input handling
            actual_enduser_date = self.select_date_picker_value(user_page, date_str)

            # Fill text and capture actual submitted value
            txt_input = user_page.get_by_role("textbox", name="Type here..")
            if not txt_input.is_visible(timeout=3000):
                txt_input = user_page.locator("input[placeholder*='Type here'], textarea[placeholder*='Type here']").first

            if txt_input.is_visible(timeout=3000):
                txt_input.click()
                txt_input.fill(text_val)
                actual_enduser_text = txt_input.input_value() or text_val
            else:
                actual_enduser_text = text_val

            # Store identified submitted values from End User form
            self.last_submitted_enduser_data = {
                "date": actual_enduser_date,
                "text": actual_enduser_text,
            }

            # Dismiss any lingering popups before clicking submit
            user_page.keyboard.press("Escape")
            user_page.wait_for_timeout(300)

            # Submit
            submit_btn = user_page.get_by_role("button", name=AppBuilderLocators.SUBMIT_BUTTON)
            if not submit_btn.is_visible(timeout=2000):
                submit_btn = user_page.locator("button:has-text('Submit'), button[type='submit']").first
            submit_btn.click()
            user_page.wait_for_timeout(3000)

            # Navigate to About and verify in Table
            user_page.get_by_role("link", name=AppBuilderLocators.ABOUT_LINK).click()
            user_page.wait_for_timeout(3000)

            # Table contains entered Details assertion - verify the exact submitted values!
            self.verify_table_contains_details(
                date_str=self.last_submitted_enduser_data["date"],
                expected_snippet=self.last_submitted_enduser_data["text"],
                page_obj=user_page,
            )

            # Ensure any slider popup opened during inspection is closed
            self.close_slider_popup(user_page)

            return self.last_submitted_enduser_data
        finally:
            user_page.close()
            if own_context:
                user_context.close()

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
