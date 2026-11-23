"""Pytest fixtures configuration supporting both fresh and persistent sessions,
with automatic failure screenshot capture and Allure test reporting.
"""

import os

# Suppress Playwright Inspector and Debugger to ensure uninterrupted execution
os.environ.pop("PWDEBUG", None)
os.environ.pop("PLAYWRIGHT_INSPECT", None)
os.environ.pop("npm_config_pwdebug", None)

try:
    import playwright._impl.utils.debug as _pw_debug
    _pw_debug._debug_mode = ""
except Exception:
    pass

import time
import webbrowser
from pathlib import Path
from typing import Generator
import pytest
from playwright.sync_api import BrowserContext, Page, Playwright
from pages.login_page import LoginPage
from pages.spreadsheet_page import SpreadsheetPage
from pages.team_tracker_page import TeamTrackerPage
from pages.app_builder_page import AppBuilderPage
from utils.browser_factory import launch_persistent_browser
from utils.config import HEADLESS, USER_DATA_DIR


@pytest.fixture
def login_page(page: Page) -> LoginPage:
    """Provide an initialized LoginPage instance using clean page."""
    return LoginPage(page)


@pytest.fixture
def spreadsheet_page(page: Page) -> SpreadsheetPage:
    """Provide an initialized SpreadsheetPage instance."""
    return SpreadsheetPage(page)


@pytest.fixture(scope="session")
def persistent_context(playwright: Playwright) -> Generator[BrowserContext, None, None]:
    """Provide a persistent browser context retaining Google session across tests."""
    context, _ = launch_persistent_browser(
        playwright,
        user_data_dir=USER_DATA_DIR,
        headless=HEADLESS,
    )
    yield context
    context.close()


@pytest.fixture
def persistent_page(persistent_context: BrowserContext) -> Generator[Page, None, None]:
    """Provide an active page within the persistent session context."""
    page = persistent_context.pages[0] if persistent_context.pages else persistent_context.new_page()
    yield page


@pytest.fixture
def team_tracker_page(persistent_page: Page) -> TeamTrackerPage:
    """Provide an initialized TeamTrackerPage instance."""
    return TeamTrackerPage(persistent_page)


@pytest.fixture
def app_builder_page(persistent_page: Page) -> AppBuilderPage:
    """Provide an initialized AppBuilderPage instance."""
    return AppBuilderPage(persistent_page)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture screenshot on scenario failure and attach directly to Allure report."""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        page = item.funcargs.get("persistent_page") or item.funcargs.get("page")
        if page:
            reports_dir = Path("reports/screenshots")
            reports_dir.mkdir(parents=True, exist_ok=True)
            screenshot_name = f"{item.name}_{int(time.time())}.png"
            screenshot_path = reports_dir / screenshot_name
            try:
                page.screenshot(path=str(screenshot_path))
                try:
                    import allure
                    allure.attach.file(
                        str(screenshot_path),
                        name=f"Failure Screenshot - {item.name}",
                        attachment_type=allure.attachment_type.PNG,
                    )
                except Exception:
                    pass
            except Exception:
                pass


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    """Automatically process failure videos/clean passed videos and report Allure results."""
    if session.testsfailed == 0 and exitstatus == 0:
        try:
            from utils.video_helper import clean_passed_videos
            clean_passed_videos()
        except Exception:
            pass
    else:
        try:
            from utils.video_helper import find_videos, trim_video_to_last_n_seconds
            vids = find_videos()
            if vids:
                trimmed = trim_video_to_last_n_seconds(vids[0], max_seconds=20)
                if trimmed:
                    print(f"[INFO] Processed last 20s failure video: {trimmed.name}")
        except Exception as e:
            print(f"[WARNING] Could not process failure video in sessionfinish: {e}")

    allure_dir = Path("reports/allure-results").resolve()
    print(f"\n" + "=" * 70)
    print(f"[ALLURE] Allure report results available in: {allure_dir}")
    print(f"[ALLURE] Run 'allure serve reports/allure-results' to view.")
    print("=" * 70)
