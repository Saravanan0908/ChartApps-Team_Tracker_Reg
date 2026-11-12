"""Locators for Team Tracker form submission and data table validation."""

import re


class TeamTrackerLocators:
    # Modal & Navigation
    CLOSE_MODAL_BUTTON = re.compile(r"Close modal|Close", re.IGNORECASE)
    TEAM_TRACKER_LINK = "Team Tracker"
    DEFAULT_TRACKER_CARD_ID = "1759897659342"
    VIEW_BUTTON = re.compile(r"view", re.IGNORECASE)

    # Form Fields
    DATE_PICKER_INPUT = re.compile(r"yyyy-mm-dd", re.IGNORECASE)
    DROPDOWN_PLACEHOLDER = "Select an option..."
    OPTION_ROLE = "option"
    DEFAULT_OPTION_NAME = "FN"
    
    # Task & Activity Textboxes
    TASK_DESCRIPTION_INPUT_INDEX = 1  # nth(1) textbox
    ACTIVITY_INPUT_NAME = "Type here.."
    
    # Submit & Status
    SUBMIT_BUTTON_EXACT_NAME = " Submit"
    SUBMIT_BUTTON_PATTERN = re.compile(r"Submit", re.IGNORECASE)
    SUBMIT_BUTTON_CSS = "button:has-text('Submit'), button[type='submit'], .p-button:has-text('Submit')"
    SUCCESS_TOAST_TEXT = "Data added to the spreadsheet"
    
    # Spreadsheet Table & Verification
    DATE_COLUMN_HEADER = re.compile(r"Date", re.IGNORECASE)
    SORT_COLUMN_ICON = ".p-sortable-column-icon"
    TABLE_CELLS = "table tbody td, .p-datatable-tbody td"
