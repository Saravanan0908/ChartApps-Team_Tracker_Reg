"""Base page class providing common methods for all page objects."""

from typing import Optional
from playwright.sync_api import Page, Response


class BasePage:
    """Base class for all Page Objects in the application."""

    def __init__(self, page: Page):
        self.page: Page = page

    def navigate(self, url: str) -> Optional[Response]:
        """Navigate to a specified URL."""
        return self.page.goto(url)

    def get_title(self) -> str:
        """Return the current page title."""
        return self.page.title()

    def get_current_url(self) -> str:
        """Return the current URL of the page."""
        return self.page.url

    def wait_for_url(self, url_or_pattern: str, timeout: Optional[float] = None) -> None:
        """Wait until page URL matches the pattern."""
        self.page.wait_for_url(url_or_pattern, timeout=timeout)

