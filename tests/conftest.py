"""Pytest fixtures configuration supporting both fresh and persistent sessions,
with automatic failure screenshot capture and Azure HTML test reporting.
"""

import time
import webbrowser
from pathlib import Path
from typing import Generator
import pytest
from playwright.sync_api import BrowserContext, Page, Playwright
from pages.login_page import LoginPage
from pages.spreadsheet_page import SpreadsheetPage
from pages.team_tracker_page import TeamTrackerPage
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


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture screenshot on scenario failure and attach to Azure HTML report."""
    outcome = yield
    report = outcome.get_result()
    extras = getattr(report, "extras", [])

    if report.when == "call" and report.failed:
        page = item.funcargs.get("persistent_page") or item.funcargs.get("page")
        if page:
            reports_dir = Path("reports/screenshots")
            reports_dir.mkdir(parents=True, exist_ok=True)
            screenshot_name = f"{item.name}_{int(time.time())}.png"
            screenshot_path = reports_dir / screenshot_name
            try:
                page.screenshot(path=str(screenshot_path))
                from pytest_html import extras as html_extras
                extras.append(html_extras.image(str(screenshot_path), name="Failure Screenshot"))
                extras.append(html_extras.html(f"<div style='color:#e53e3e;font-weight:bold;margin:5px 0;'>❌ Scenario Failed: {item.name}</div>"))
            except Exception:
                pass
        report.extras = extras


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    """Automatically open the Azure HTML report in the default browser when tests fail."""
    # Check if any test in the session failed
    if session.testsfailed > 0 or exitstatus != 0:
        report_path = Path("reports/azure_test_report.html").resolve()
        if report_path.exists():
            print(f"\n" + "=" * 70)
            print(f"[TEST FAILURE DETECTED] {session.testsfailed} scenario(s) failed.")
            print(f"[INFO] Automatically opening Azure HTML Report: {report_path}")
            print("=" * 70)
            try:
                webbrowser.open(report_path.as_uri())
            except Exception as e:
                print(f"[WARNING] Could not automatically open browser: {e}")
