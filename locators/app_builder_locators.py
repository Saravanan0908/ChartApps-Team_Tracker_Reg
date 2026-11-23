"""Locators for New App Creation, Editor Configuration, and End-User verification."""

import re


class AppBuilderLocators:
    """Locators for ChartApps App Builder / Editor and End-User flows."""

    # Dashboard & App Creation Modal
    CREATE_APP_BUTTON = re.compile(r"Create App", re.IGNORECASE)
    APP_NAME_INPUT = "input[placeholder*='App Name'], input[type='text']"
    CONNECT_GOOGLE_BUTTON = re.compile(r"Connect Your Google Account", re.IGNORECASE)
    GOOGLE_ACCOUNT_LINK_PATTERN = re.compile(r"chartapps.*@gmail", re.IGNORECASE)
    CONTINUE_BUTTON = re.compile(r"Continue", re.IGNORECASE)
    NEXT_BUTTON = re.compile(r"Next", re.IGNORECASE)
    SELECT_SPREADSHEET_BUTTON = re.compile(r"Select Your Spreadsheet", re.IGNORECASE)
    CREATE_DASHBOARD_BUTTON = re.compile(r"Create Dashboard", re.IGNORECASE)

    # Google OAuth Consent Screen Locators
    GOOGLE_OAUTH_URL_SUBSTRING = "accounts.google.com"
    GOOGLE_CONSENT_TITLE = re.compile(r"wants access to your Google Account|already has some access", re.IGNORECASE)
    GOOGLE_CONTINUE_SELECTOR = "button:has-text('Continue'), [role='button']:has-text('Continue'), div[role='button']:has-text('Continue')"
    GOOGLE_NEXT_SELECTOR = "button:has-text('Next'), [role='button']:has-text('Next')"

    # Spreadsheet Picker & Mapping
    SPREADSHEET_OPTION_NAME = "Regression Testing Automation"
    SPREADSHEET_IFRAME_CSS = "iframe[src*='picker'], iframe[name*='picker'], iframe"
    SELECT_BUTTON = re.compile(r"Select", re.IGNORECASE)
    PICKER_SELECT_CONTROL = "[role='button']:has-text('Select'), .picker-select-control-enabled, div.jfk-button:has-text('Select'), button:has-text('Select')"
    DEFAULT_SHEET = "User"
    DEFAULT_NAME_COL = "Name "
    DEFAULT_EMAIL_COL = "Email"
    DEFAULT_DETAILS_SHEET = "Regression Submition"

    # Editor Pages & Navigation
    PAGES_ICON = re.compile(r"Pages", re.IGNORECASE)
    ADD_BUTTON = re.compile(r"^Add$", re.IGNORECASE)
    PAGE_NAME_INPUT = re.compile(r"Page Name", re.IGNORECASE)
    URL_SLUG_INPUT = re.compile(r"URL Slug", re.IGNORECASE)
    SAVE_BUTTON = re.compile(r"^Save$", re.IGNORECASE)
    CLOSE_BUTTON = re.compile(r"^Close$", re.IGNORECASE)
    HEADER_LINK = "Header"
    NAVIGATION_BAR_TAB = re.compile(r"Navigation bar", re.IGNORECASE)
    HOME_LINK = "Home"
    ABOUT_LINK = "About"

    # Blocks & Axes Configuration
    NEW_BLOCK_ICON = re.compile(r"New Block", re.IGNORECASE)
    AXES_TAB = re.compile(r"Axes", re.IGNORECASE)
    DATE_BUTTON = "Date"
    TITLE_BUTTON = "Title"

    # Editor Form Submission & Table Verification
    DATETIME_INPUT = re.compile(r"yyyy-mm-dd HH:MM", re.IGNORECASE)
    DATE_INPUT = re.compile(r"yyyy-mm-dd", re.IGNORECASE)
    TYPE_HERE_INPUT = re.compile(r"Type here\.\.", re.IGNORECASE)
    SUBMIT_BUTTON = re.compile(r"Submit", re.IGNORECASE)

    # Publish & Privacy
    PUBLISH_BUTTON = re.compile(r"Publish", re.IGNORECASE)
    PRIVACY_SETTINGS_BUTTON = re.compile(r"Privacy Settings", re.IGNORECASE)
    APP_PRIVACY_CHECKBOX = re.compile(r"App privacy", re.IGNORECASE)
    ENTER_PUBLIC_URL_INPUT = re.compile(r"Enter public URL", re.IGNORECASE)

    # Deletion & Cleanup
    DELETE_APP_BUTTON = re.compile(r"Delete App", re.IGNORECASE)
    MY_APPS_LINK = re.compile(r"My Apps", re.IGNORECASE)
