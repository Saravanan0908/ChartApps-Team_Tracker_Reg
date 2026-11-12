"""Locators for ChartApps dashboard and spreadsheet operations."""

import re


class SpreadsheetLocators:
    # Navigation & Dashboard elements
    DASHBOARD_HEADING = re.compile(r"Dashboard|My Charts|Sheets|Spreadsheets", re.IGNORECASE)
    CONNECT_GOOGLE_BTN = re.compile(r"Connect Google|Connect Google Sheet|Sign in with Google", re.IGNORECASE)
    
    # Spreadsheet & Table elements
    SPREADSHEET_SECTION = "table, [data-testid='spreadsheet-view'], .spreadsheet-container, .charts-container"
    ADD_SPREADSHEET_BUTTON = re.compile(r"Add Spreadsheet|New Chart|Import Sheet|Select Sheet", re.IGNORECASE)
    SPREADSHEET_TABLE = "table"
    SPREADSHEET_ROWS = "table tbody tr"
    SPREADSHEET_HEADERS = "table thead th"
    SHEET_SELECT_DROPDOWN = "[aria-label='Select Sheet'], select"
    
    # Success / Connection state indicators
    ACCOUNT_CONNECTED_BADGE = re.compile(r"Connected|Account|Logout|Sign out", re.IGNORECASE)

