"""Test data definitions for login tests."""

import json
from pathlib import Path

DATA_FILE_PATH = Path(__file__).parent / "login_data.json"
EXAMPLE_FILE_PATH = Path(__file__).parent / "login_data.example.json"


def load_json_data() -> dict:
    target_file = DATA_FILE_PATH if DATA_FILE_PATH.exists() else EXAMPLE_FILE_PATH
    if target_file.exists():
        with open(target_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


_json_data = load_json_data()
_user = _json_data.get("user", {})


class LoginTestData:
    """Provides test credentials for authentication test cases."""
    EMAIL: str = _user.get("email", "your_email@gmail.com")
    PASSWORD: str = _user.get("password", "your_password")
