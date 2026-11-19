"""Base Page Object Module.

This is the foundational class that all other Page Objects inherit from.
It encapsulates common browser interactions (navigation, waiting, title checks, screenshots)
so that individual page classes can focus exclusively on their specific page elements and workflows.
"""

from pathlib import Path
from typing import Optional
from playwright.sync_api import Page, Response


class BasePage:
    """Base class for all Page Objects in the POM architecture.
    
    Attributes:
        page (Page): The Playwright Page instance used to interact with the browser.
    """

    def __init__(self, page: Page):
        """Initialize the BasePage with an active Playwright page.
        
        Args:
            page (Page): The active browser page instance.
        """
        self.page: Page = page

    def navigate(self, url: str) -> Optional[Response]:
        """Navigate the browser to a target URL.
        
        Args:
            url (str): The complete destination URL (e.g., 'https://chartapps.app/dashboard').
            
        Returns:
            Optional[Response]: The HTTP response object returned by Playwright.
        """
        return self.page.goto(url)

    def get_title(self) -> str:
        """Get the HTML title of the current page.
        
        Returns:
            str: Page title string (e.g. 'Web Application').
        """
        return self.page.title()

    def get_current_url(self) -> str:
        """Get the active URL currently displayed in the address bar.
        
        Returns:
            str: Current URL string.
        """
        return self.page.url

    def wait_for_url(self, url_or_pattern: str, timeout: Optional[float] = None) -> None:
        """Wait until the current URL matches a specific URL or regex pattern.
        
        Args:
            url_or_pattern (str): The URL substring or regex pattern to wait for.
            timeout (Optional[float]): Maximum wait time in milliseconds.
        """
        self.page.wait_for_url(url_or_pattern, timeout=timeout)

    def wait_for_dom_ready(self) -> None:
        """Wait for the HTML DOM content to finish loading."""
        self.page.wait_for_load_state("domcontentloaded")

    def take_screenshot(self, filepath: str) -> str:
        """Capture a screenshot of the current page and save to disk.
        
        Args:
            filepath (str): The destination path for the screenshot image file.
            
        Returns:
            str: Saved screenshot path.
        """
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.page.screenshot(path=str(path))
        return str(path)
