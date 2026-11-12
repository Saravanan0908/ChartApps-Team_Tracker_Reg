"""Page Object representing the Authentication and Login page."""

import re
from typing import Optional
from playwright.sync_api import Locator, Page
from constants.urls import AppUrls
from locators.login_locators import LoginLocators
from pages.base_page import BasePage


class LoginPage(BasePage):
    """Encapsulates actions and locators for ChartApps login and Google authentication."""

    def __init__(self, page: Page):
        super().__init__(page)

    # --- Locators ---
    @property
    def google_sign_in_button(self) -> Locator:
        return self.page.get_by_role("button", name=LoginLocators.GOOGLE_SIGN_IN_PATTERN)

    @property
    def email_or_phone_input(self) -> Locator:
        return self.page.get_by_role("textbox", name=LoginLocators.EMAIL_OR_PHONE_INPUT_NAME)

    @property
    def next_button(self) -> Locator:
        return self.page.get_by_role("button", name=LoginLocators.NEXT_BUTTON_NAME)

    @property
    def password_input(self) -> Locator:
        return self.page.locator(LoginLocators.PASSWORD_SELECTOR)

    @property
    def password_next_button(self) -> Locator:
        return self.page.locator(LoginLocators.PASSWORD_NEXT_BUTTON_SELECTOR)

    # --- Actions ---
    def open_auth_page(self) -> None:
        """Navigate to the auth page through dashboard redirect flow."""
        self.navigate(AppUrls.DASHBOARD_URL)
        if "/auth" not in self.page.url:
            self.navigate(AppUrls.AUTH_URL)

    def is_connect_google_visible(self) -> bool:
        """Check if Google Sign In / Connect button is displayed."""
        try:
            return self.google_sign_in_button.first.is_visible(timeout=5000)
        except Exception:
            return False

    def click_google_sign_in(self) -> None:
        """Click the Google sign in / connect button."""
        self.google_sign_in_button.first.click()

    def enter_email_or_phone(self, email_or_phone: str) -> None:
        """Click and fill the email or phone input box."""
        self.email_or_phone_input.click()
        self.email_or_phone_input.fill(email_or_phone)

    def click_next(self) -> None:
        """Click the 'Next' button."""
        self.next_button.first.click()

    def enter_password(self, password: str) -> None:
        """Wait for password input to appear, click, and fill it."""
        self.password_input.first.wait_for(state="visible", timeout=15000)
        self.password_input.first.click()
        self.password_input.first.fill(password)

    def click_password_next(self) -> None:
        """Click the Next button after entering password."""
        self.password_next_button.first.click()

    def login_with_google(self, email_or_phone: str, password: str) -> None:
        """Perform complete Google sign-in workflow (Email -> Next -> Password -> Next)."""
        self.click_google_sign_in()
        self.enter_email_or_phone(email_or_phone)
        self.click_next()
        self.enter_password(password)
        self.click_password_next()

    def wait_for_auth_completion(self, timeout_ms: int = 180000) -> bool:
        """Wait for user to complete manual Google authentication and return to dashboard."""
        try:
            self.page.wait_for_url(re.compile(r"chartapps\.app/dashboard(?!/auth)"), timeout=timeout_ms)
            return True
        except Exception:
            return "dashboard" in self.page.url and "auth" not in self.page.url

    def is_authenticated(self) -> bool:
        """Check whether the user is currently on the authenticated dashboard."""
        return "dashboard" in self.page.url and "auth" not in self.page.url
