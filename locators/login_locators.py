"""Locators for login and authentication pages."""

import re


class LoginLocators:
    # Role-based names & selector patterns for Auth buttons
    GOOGLE_SIGN_IN_PATTERN = re.compile(r"Google|Sign in with Google|Connect Google", re.IGNORECASE)
    CONNECT_GOOGLE_BUTTON_NAME: str = "Google Sign in with Google"
    
    # Google Account input fields
    EMAIL_OR_PHONE_INPUT_NAME: str = "Email or phone"
    NEXT_BUTTON_NAME: str = "Next"
    PASSWORD_INPUT_NAME: str = "Enter your password"
    PASSWORD_SELECTOR: str = "input[type='password'], input[name='Passwd'], input[autocomplete='current-password']"
    PASSWORD_NEXT_BUTTON_SELECTOR: str = "#passwordNext, button:has-text('Next')"
