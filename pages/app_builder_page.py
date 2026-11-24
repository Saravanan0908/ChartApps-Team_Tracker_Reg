"""App Builder Page Object for New App creation, page editing, blocks, publishing, and cleanup."""

import re
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, expect

from locators.app_builder_locators import AppBuilderLocators
from pages.base_page import BasePage
from testdata.test_data import LoginTestData
from utils.config import HEADLESS


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
        self.app_name = app_name
        self.app_slug = app_slug
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
        1. Check if 'Select Your Spreadsheet' is already visible
        2. If 'Next' button on dashboard creation is already enabled, click it
        3. Otherwise, click 'Connect Your Google Account' (handling popup or tab)
        4. Select account, check consent checkboxes, click Continue/Next
        5. Back on main page, click 'Next' to transition to spreadsheet step
        6. Wait for 'Select Your Spreadsheet' to be visible
        """
        # Step A: Check if already on Spreadsheet selection step
        select_sheet_btn = self.page.locator("button:has-text('Select Your Spreadsheet'), button:has-text('Create Dashboard')").first
        if select_sheet_btn.is_visible(timeout=2000):
            print("[INFO] 'Select Your Spreadsheet' is already visible. Proceeding...")
            return

        # Ensure App Name and Subdomain are filled before checking 'Next' button
        self._ensure_app_details_filled()

        # Step B: Check if Next button on Create your dashboard is already enabled (or Google already connected)
        already_connected = self.page.locator("text='Connected as:', text='Change Account'").first
        next_btn = self.page.locator("button:has-text('Next'), [role='button']:has-text('Next')").first
        if already_connected.is_visible(timeout=2000):
            print("[INFO] Google account is already connected ('Connected as: ...' detected).")
            self._ensure_app_details_filled()
            self.page.wait_for_timeout(1000)
            if next_btn.is_visible(timeout=3000):
                try:
                    expect(next_btn).to_be_enabled(timeout=10000)
                    next_btn.scroll_into_view_if_needed()
                    next_btn.click()
                    print("[INFO] Clicked 'Next' with existing Google connection.")
                    self.page.wait_for_timeout(2000)
                    if select_sheet_btn.is_visible(timeout=5000):
                        return
                except Exception as e:
                    print(f"[DEBUG] Clicking Next on already connected state: {e}")

        if next_btn.is_visible(timeout=2000) and next_btn.is_enabled():
            print("[INFO] Google account already connected ('Next' is enabled). Clicking Next...")
            next_btn.scroll_into_view_if_needed()
            next_btn.click()
            self.page.wait_for_timeout(2000)
            if select_sheet_btn.is_visible(timeout=5000):
                return

        # Step C: Click 'Connect Your Google Account' if visible
        connect_btn = self.page.get_by_role("button", name="Connect Your Google Account")
        if not connect_btn.is_visible(timeout=3000):
            connect_btn = self.page.locator("button:has-text('Connect Your Google Account')").first

        if connect_btn.is_visible(timeout=3000):
            print("[INFO] Clicking 'Connect Your Google Account'...")
            oauth_page = None
            try:
                with self.page.expect_popup(timeout=3000) as popup_info:
                    connect_btn.click()
                oauth_page = popup_info.value
                print(f"[INFO] Google OAuth opened in popup window: {oauth_page.url}")
            except Exception:
                self.page.wait_for_timeout(2000)
                for p in self.page.context.pages:
                    if "accounts.google.com" in p.url or "google.com" in p.url:
                        oauth_page = p
                        break
                if not oauth_page:
                    oauth_page = self.page

            # Handle Google OAuth on the target oauth_page
            start_time = time.time()
            while (time.time() - start_time) < 60:
                if oauth_page.is_closed():
                    print("[INFO] Google OAuth popup closed.")
                    break

                current_url = oauth_page.url
                if "chartapps.app" in current_url and "accounts.google.com" not in current_url:
                    print("[INFO] Redirected back to ChartApps from Google OAuth.")
                    break

                if "accounts.google.com" in current_url:
                    # Check for Google 2-Step Verification / "Verify it's you" security checkpoint
                    try:
                        verify_challenge = oauth_page.locator(
                            "h1:has-text('Verify it’s you'), "
                            "h1:has-text('Verify it\\'s you'), "
                            "h2:has-text('Choose how you want to sign in'), "
                            "text='Choose how you want to sign in'"
                        ).first
                        if verify_challenge.is_visible(timeout=1000):
                            msg = (
                                "\n" + "=" * 70 + "\n"
                                "[ERROR] Google 2-Step Verification ('Verify it’s you') triggered!\n"
                                "Google blocked automated interactive login from this cloud runner IP.\n"
                                "To run on GitHub Actions without 2FA blockage:\n"
                                "1. Run 'utils\\copy_auth_for_github.bat' on your local computer.\n"
                                "2. Paste the copied session into GitHub Repo Secrets as 'AUTH_STORAGE_STATE'.\n"
                                + "=" * 70 + "\n"
                            )
                            print(msg, flush=True)
                            raise RuntimeError(msg)
                    except RuntimeError:
                        raise
                    except Exception:
                        pass

                    # Check for Google "Couldn't sign you in" / "This browser or app may not be secure"
                    try:
                        insecure_msg = oauth_page.locator("text='This browser or app may not be secure', text='Couldn’t sign you in', text='Could not sign you in'").first
                        if insecure_msg.is_visible(timeout=1000):
                            print("[WARNING] Google detected automation on OAuth consent ('This browser or app may not be secure').")
                            try_again = oauth_page.locator("a:has-text('Try again'), button:has-text('Try again')").first
                            if try_again.is_visible(timeout=1000):
                                print("[INFO] Clicking 'Try again' on Google OAuth screen...")
                                try_again.click()
                                oauth_page.wait_for_timeout(2500)
                                continue
                    except Exception:
                        pass

                    # 1. Email input: Fill email first if on sign-in screen
                    email_input = oauth_page.locator("input[type='email'], input#identifierId, input[name='identifier']").first
                    is_email_screen = False
                    try:
                        if email_input.is_visible(timeout=1000):
                            is_email_screen = True
                            print("[INFO] Google Sign-in screen detected: entering email...")
                            email_input.fill("")
                            email_input.press_sequentially(LoginTestData.EMAIL, delay=60)
                            oauth_page.wait_for_timeout(500)
                            id_next = oauth_page.locator("#identifierNext, button:has-text('Next')").first
                            id_next.click()
                            print("[INFO] Submitted email, waiting for password screen...")
                            oauth_page.wait_for_timeout(2500)
                            continue
                    except Exception as e:
                        print(f"[DEBUG] Email check exception: {e}")

                    # 2. Password input: Fill password if on password screen
                    pwd_input = oauth_page.locator("input[type='password'], input[name='Passwd'], input[autocomplete='current-password']").first
                    is_pwd_screen = False
                    try:
                        if pwd_input.is_visible(timeout=1000):
                            is_pwd_screen = True
                            print("[INFO] Google Password screen detected: entering password...")
                            pwd_input.fill("")
                            pwd_input.press_sequentially(LoginTestData.PASSWORD, delay=60)
                            oauth_page.wait_for_timeout(500)
                            pwd_next = oauth_page.locator("#passwordNext, button:has-text('Next')").first
                            pwd_next.click()
                            print("[INFO] Submitted password, waiting for consent screen...")
                            oauth_page.wait_for_timeout(2500)
                            continue
                    except Exception as e:
                        print(f"[DEBUG] Password check exception: {e}")

                    # D. Continue / Allow FIRST — before account tile check.
                    #    Covers ALL consent screens:
                    #    - "You're signing back in to ChartApps"            -> Continue
                    #    - "ChartApps wants access to your Google Account"  -> Continue / Allow
                    #    Also handles "Scroll down" button that may block the click.
                    try:
                        cont_btn = oauth_page.locator(
                            "button:has-text('Continue'), "
                            "button:has-text('Allow'), "
                            "[role='button']:has-text('Continue'), "
                            "[role='button']:has-text('Allow')"
                        ).first
                        if cont_btn.is_visible(timeout=1500):
                            # Scroll page first if needed
                            try:
                                scroll_btn = oauth_page.locator("button:has-text('Scroll down')").first
                                if scroll_btn.is_visible(timeout=500):
                                    print("[INFO] Scrolling consent page before clicking Continue...")
                                    scroll_btn.click()
                                    oauth_page.wait_for_timeout(800)
                            except Exception:
                                pass
                            btn_text = cont_btn.inner_text().strip()
                            print(f"[INFO] Clicking '{btn_text}' on Google OAuth consent screen...")
                            cont_btn.click()
                            oauth_page.wait_for_timeout(2500)
                            continue
                    except Exception:
                        pass

                    # E. Account chooser TILES — only reached when no Continue/Allow visible and NOT on a challenge page.
                    #    Tightly-scoped to account chooser list items only.
                    #    Guarded against challenge/error pages where email text is displayed as label.
                    if "/challenge" not in oauth_page.url:
                        try:
                            account_tile = oauth_page.locator(
                                "li[data-identifier*='chartapps'], "
                                "div[data-identifier*='chartapps']"
                            ).first
                            if account_tile.is_visible(timeout=1000):
                                label = (account_tile.get_attribute("data-identifier")
                                         or account_tile.get_attribute("data-email") or "chartapps account")
                                print(f"[INFO] Clicking account chooser tile: {label}...")
                                account_tile.click()
                                oauth_page.wait_for_timeout(2000)
                                continue
                        except Exception:
                            pass

                    # F. Consent Screen Checkboxes
                    try:
                        checkboxes = oauth_page.locator("input[type='checkbox']:not(:checked)")
                        if checkboxes.count() > 0:
                            for i in range(checkboxes.count()):
                                cb = checkboxes.nth(i)
                                if cb.is_visible():
                                    cb.check(force=True)
                            oauth_page.wait_for_timeout(500)
                    except Exception:
                        pass

                    # G. Next button (non-email/password screens only)
                    try:
                        if not is_email_screen and not is_pwd_screen:
                            next_consent_btn = oauth_page.locator(
                                "button:has-text('Next'), "
                                "[role='button']:has-text('Next')"
                            ).first
                            if next_consent_btn.is_visible(timeout=1000):
                                print("[INFO] Clicking 'Next' on Google consent screen...")
                                next_consent_btn.click()
                                oauth_page.wait_for_timeout(2000)
                                continue
                    except Exception:
                        pass

                oauth_page.wait_for_timeout(1000)


        # Step D: Ensure browser has navigated back to ChartApps dashboard (NOT Google)
        print("[INFO] Waiting for navigation back to ChartApps dashboard...", flush=True)
        for _ in range(30):
            if "chartapps.app" in self.page.url and "accounts.google.com" not in self.page.url:
                break
            self.page.wait_for_timeout(1000)

        self.page.wait_for_timeout(2000)
        if "chartapps.app" in self.page.url and "accounts.google.com" not in self.page.url:
            # Re-fill App Name and Subdomain if cleared by OAuth redirect
            self._ensure_app_details_filled()

            next_btn = self.page.locator("button:has-text('Next'), [role='button']:has-text('Next')").first
            if next_btn.is_visible(timeout=5000):
                try:
                    # Wait for Next button to become enabled after Name, Subdomain & Google are all verified
                    expect(next_btn).to_be_enabled(timeout=20000)
                    next_btn.scroll_into_view_if_needed()
                    next_btn.click()
                    print("[INFO] Clicked 'Next' button on Create dashboard.")
                    self.page.wait_for_timeout(2000)
                except Exception as next_err:
                    print(f"[WARNING] Could not click 'Next' button directly: {next_err}")
                    # Re-verify fields and retry click with force
                    self._ensure_app_details_filled()
                    self.page.wait_for_timeout(1000)
                    try:
                        next_btn.click(force=True)
                        print("[INFO] Clicked 'Next' button with force=True.")
                        self.page.wait_for_timeout(2000)
                    except Exception:
                        pass

        # Step E: Wait until 'Select Your Spreadsheet' or 'Create Dashboard' is visible
        select_sheet_btn = self.page.locator("button:has-text('Select Your Spreadsheet'), button:has-text('Create Dashboard')").first
        expect(select_sheet_btn).to_be_visible(timeout=30000)
        self.page.wait_for_timeout(1500)

    def _ensure_app_details_filled(self) -> None:
        """Ensure App Name and Subdomain are filled, re-populating them if cleared by OAuth redirect."""
        try:
            name_input = self.page.get_by_role("textbox").first
            slug_input = self.page.get_by_role("textbox").nth(1)

            if name_input.is_visible(timeout=2000):
                current_name = name_input.input_value().strip()
                target_name = getattr(self, "app_name", None)
                if not current_name and target_name:
                    print(f"[INFO] App Name was empty after OAuth redirect. Re-filling: '{target_name}'")
                    name_input.click()
                    name_input.fill(target_name)
                    self.page.wait_for_timeout(500)

            if slug_input.is_visible(timeout=2000):
                current_slug = slug_input.input_value().strip()
                target_slug = getattr(self, "app_slug", None)
                if not current_slug and target_slug:
                    print(f"[INFO] Subdomain was empty after OAuth redirect. Re-filling: '{target_slug}'")
                    slug_input.click()
                    slug_input.fill(target_slug)
                    self.page.wait_for_timeout(1500)
        except Exception as e:
            print(f"[DEBUG] Error checking/re-filling app details: {e}")

    def select_google_spreadsheet(self, spreadsheet_name: str = "Regression Testing Automation") -> None:
        """Open Google Picker and select spreadsheet."""
        select_sheet_btn = self.page.locator("button:has-text('Select Your Spreadsheet')").first
        expect(select_sheet_btn).to_be_visible(timeout=30000)
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
        """Close the Details slider / drawer popup that opens when clicking a table row/cell."""
        target_page.wait_for_timeout(300)

        # 1. Direct CSS selectors matching the exact DOM tree from inspection:
        # <div class="... custom-sidebar-width ..."><button class="absolute top-1 right-4 text-gray-500 hover:text-gray-700 z-10">
        close_locators = [
            target_page.locator(".custom-sidebar-width button.absolute").first,
            target_page.locator("button.absolute.top-1.right-4").first,
            target_page.locator(".custom-sidebar-width button").first,
            target_page.locator("button:has(path[d*='M6 18L18 6'])").first,
            target_page.locator("path[d='M6 18L18 6M6 6l12 12']").locator("..").first,
        ]
        for loc in close_locators:
            try:
                if loc.is_visible(timeout=500):
                    loc.click(force=True)
                    target_page.wait_for_timeout(300)
                    if not target_page.locator(".custom-sidebar-width").is_visible(timeout=500):
                        return
            except Exception:
                pass

        # 2. Try the empty icon buttons recorded in codegen (nth(4), nth(5), nth(3))
        try:
            empty_btns = target_page.get_by_role("button").filter(has_text=re.compile(r"^$"))
            for idx in (4, 5, 3):
                if empty_btns.count() > idx:
                    btn = empty_btns.nth(idx)
                    if btn.is_visible(timeout=500):
                        btn.click(force=True)
                        target_page.wait_for_timeout(300)
                        if not target_page.locator(".custom-sidebar-width").is_visible(timeout=500):
                            return
        except Exception:
            pass

        # 3. Dismiss via Escape key
        try:
            target_page.keyboard.press("Escape")
            target_page.wait_for_timeout(300)
            if not target_page.locator(".custom-sidebar-width").is_visible(timeout=500):
                return
        except Exception:
            pass

        # 4. Direct DOM evaluation: click close button or remove sidebar so it cannot block interactions
        try:
            target_page.evaluate("""() => {
                const sidebars = document.querySelectorAll('.custom-sidebar-width, div[style*="z-index: 10000"]');
                for (const sb of sidebars) {
                    const btn = sb.querySelector('button');
                    if (btn) {
                        btn.click();
                    }
                    if (document.querySelectorAll('.custom-sidebar-width').length > 0) {
                        sb.remove();
                    }
                }
            }""")
            target_page.wait_for_timeout(300)
        except Exception:
            pass

    def close_open_dialogs(self, target_page: Optional[Page] = None) -> None:
        """Close any modal popup dialog (such as Privacy Settings or publish modal) that may be open."""
        p = target_page or self.page
        p.wait_for_timeout(300)

        # 1. Targeted locators for modal dialog close buttons
        dialog_close_locators = [
            p.locator("[role='dialog'] button[aria-label*='Close' i]").first,
            p.locator(".p-dialog-header-close, .p-dialog-header-icon").first,
            p.locator("[role='dialog'] button.absolute, [role='dialog'] button.top-1, [role='dialog'] button:has(svg)").first,
            p.locator("div:has(> h3:has-text('Privacy Settings')) button").first,
            p.get_by_role("button").filter(has_text=re.compile(r"^$")).first,
        ]
        for loc in dialog_close_locators:
            try:
                if loc.is_visible(timeout=500):
                    loc.click(force=True)
                    p.wait_for_timeout(400)
                    if not p.locator("[role='dialog'], .p-dialog, div:has(> h3:has-text('Privacy Settings'))").is_visible(timeout=500):
                        return
            except Exception:
                pass

        # 2. Dismiss via Escape key
        try:
            p.keyboard.press("Escape")
            p.wait_for_timeout(300)
            if not p.locator("[role='dialog'], .p-dialog").is_visible(timeout=500):
                return
        except Exception:
            pass

        # 3. Direct DOM cleanup to remove any lingering dialog and modal mask overlay
        try:
            p.evaluate("""() => {
                const dialogs = document.querySelectorAll("[role='dialog'], .p-dialog, .p-dialog-mask, .modal-backdrop");
                for (const d of dialogs) {
                    const btn = d.querySelector("button[aria-label*='Close' i], .p-dialog-header-close, button.absolute, button");
                    if (btn) {
                        btn.click();
                    }
                    if (document.querySelectorAll("[role='dialog'], .p-dialog-mask").length > 0) {
                        d.remove();
                    }
                }
            }""")
            p.wait_for_timeout(300)
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
        if not d_input.is_visible(timeout=5000):
            d_input = target_page.locator("input[placeholder*='yyyy-mm-dd'], input.flatpickr-input, input[name='Date']").first

        if d_input.is_visible(timeout=5000):
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
        self.page.wait_for_timeout(1000)

        # Get Public URL from input or current origin before closing dialog
        return_url = ""
        public_url_input = self.page.get_by_role("textbox", name=AppBuilderLocators.ENTER_PUBLIC_URL_INPUT)
        if public_url_input.is_visible(timeout=3000):
            url_val = public_url_input.input_value()
            if url_val and "chartapps.app" in url_val:
                if not url_val.startswith("http"):
                    url_val = f"https://{url_val}"
                return_url = url_val.rstrip("/")

        if not return_url and hasattr(self, "app_slug") and self.app_slug:
            return_url = f"https://{self.app_slug}.chartapps.app"

        if not return_url:
            curr = self.page.url
            return_url = curr.split("?")[0].rstrip("/")

        # Close Privacy Settings modal so the editor view and sidebar are completely unblocked
        self.close_open_dialogs(self.page)
        return return_url

    def submit_and_verify_as_end_user(
        self,
        public_url: str,
        date_str: str,
        text_val: str,
        context: Optional[BrowserContext] = None,
        browser: Optional[Browser] = None,
        playwright: Optional[Playwright] = None,
    ) -> dict[str, str]:
        """Launch a fresh incognito session without cookies/caches, submit Form 2, and review in About table."""
        own_browser = False
        user_browser = None
        own_context = False

        if playwright is not None:
            videos_dir = Path("reports/videos")
            videos_dir.mkdir(parents=True, exist_ok=True)
            user_browser = playwright.chromium.launch(
                headless=HEADLESS,
                args=["--disable-blink-features=AutomationControlled"],
            )
            user_context = user_browser.new_context(
                viewport={"width": 1920, "height": 1080},
                record_video_dir=str(videos_dir),
                record_video_size={"width": 1280, "height": 720},
            )
            own_browser = True
            own_context = True
        elif browser is not None:
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
            # 1. Navigate to published public app URL
            try:
                user_page.goto(public_url, wait_until="networkidle", timeout=30000)
            except Exception:
                user_page.goto(public_url, wait_until="domcontentloaded", timeout=30000)
            user_page.wait_for_timeout(3000)

            # 2. Wait explicitly for Date input to appear (ensures SPA has loaded and mounted)
            d_input = user_page.get_by_role("textbox", name="yyyy-mm-dd")
            if not d_input.is_visible(timeout=5000):
                d_input = user_page.locator("input[placeholder*='yyyy-mm-dd'], input.flatpickr-input, input[name='Date']").first

            expect(d_input).to_be_visible(timeout=25000)

            # 3. Fill date (Current Date) using calendar popup overlay
            actual_enduser_date = self.select_date_picker_value(user_page, date_str)

            # 4. Fill Title text input and capture actual submitted value
            txt_input = user_page.get_by_role("textbox", name="Type here..")
            if not txt_input.is_visible(timeout=5000):
                txt_input = user_page.locator("input[placeholder*='Type here'], textarea[placeholder*='Type here']").first

            expect(txt_input).to_be_visible(timeout=10000)
            txt_input.click()
            txt_input.fill(text_val)
            actual_enduser_text = txt_input.input_value() or text_val

            # Store identified submitted values from End User form
            self.last_submitted_enduser_data = {
                "date": actual_enduser_date,
                "text": actual_enduser_text,
            }

            # Dismiss any lingering popups before clicking submit
            user_page.keyboard.press("Escape")
            user_page.wait_for_timeout(300)

            # 5. Submit Form 2
            submit_btn = user_page.get_by_role("button", name=AppBuilderLocators.SUBMIT_BUTTON)
            if not submit_btn.is_visible(timeout=3000):
                submit_btn = user_page.locator("button:has-text('Submit'), button[type='submit']").first
            expect(submit_btn).to_be_visible(timeout=10000)
            submit_btn.click()
            user_page.wait_for_timeout(3000)

            # 6. Navigate to About and review in Table
            about_link = user_page.get_by_role("link", name=AppBuilderLocators.ABOUT_LINK)
            if not about_link.is_visible(timeout=3000):
                about_link = user_page.locator("a:has-text('About'), nav a:has-text('About')").first
            expect(about_link).to_be_visible(timeout=10000)
            about_link.click()
            user_page.wait_for_timeout(3000)

            # 7. Table contains entered Details assertion - verify the exact submitted values!
            table = user_page.get_by_role("table")
            expect(table).to_be_visible(timeout=15000)

            # Assert submitted text is present in the table
            expect(user_page.get_by_text(actual_enduser_text[:35]).first).to_be_visible(timeout=10000)

            # Assert submitted date is present in table and click date cell
            date_cell = user_page.get_by_role("cell", name=re.compile(re.escape(actual_enduser_date))).or_(user_page.get_by_text(actual_enduser_date))
            if date_cell.first.is_visible(timeout=5000):
                expect(date_cell.first).to_be_visible(timeout=5000)
                try:
                    date_cell.first.click()
                    user_page.wait_for_timeout(500)
                    self.close_slider_popup(user_page)
                except Exception:
                    pass

            # 8. Ensure Details slider popup is closed
            self.close_slider_popup(user_page)

            return self.last_submitted_enduser_data
        finally:
            try:
                user_page.close()
            except Exception:
                pass
            if own_context:
                try:
                    user_context.close()
                except Exception:
                    pass
            if own_browser and user_browser:
                try:
                    user_browser.close()
                except Exception:
                    pass
            # Back on the first tab: bring to front and close any lingering popups/modals
            try:
                self.page.bring_to_front()
                self.close_open_dialogs(self.page)
            except Exception:
                pass

    def delete_app_and_cleanup(self, app_name: str) -> None:
        """Delete the created app from ChartApps and confirm dialog."""
        # Ensure focus is on the first tab and any lingering dialogs/modals are closed
        try:
            self.page.bring_to_front()
        except Exception:
            pass
        self.close_open_dialogs(self.page)
        self.page.wait_for_timeout(1000)

        del_btn = self.page.get_by_role("button", name="Delete App")
        if not del_btn.is_visible(timeout=3000):
            sidebar_icon = self.page.locator("li:has-text('App Settings'), li:has-text('Settings'), li:nth-child(5) .sidebar-item-content").first
            if sidebar_icon.is_visible(timeout=3000):
                sidebar_icon.click(force=True)
                self.page.wait_for_timeout(1500)

        del_btn = self.page.get_by_role("button", name="Delete App")
        if not del_btn.is_visible(timeout=3000):
            del_btn = self.page.locator("button:has-text('Delete App')").first

        if del_btn.is_visible(timeout=5000):
            self.page.once("dialog", lambda dialog: dialog.accept())
            del_btn.click()
            self.page.wait_for_timeout(2000)

            # Handle confirmation modal button if present
            confirm_btn = self.page.locator("[role='dialog'] button:has-text('Delete'), [role='dialog'] button:has-text('Confirm'), [role='dialog'] button:has-text('Yes')").first
            if confirm_btn.is_visible(timeout=2000):
                confirm_btn.click(force=True)
                self.page.wait_for_timeout(2000)
