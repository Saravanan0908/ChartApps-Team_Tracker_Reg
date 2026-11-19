"""Test data definitions for login tests."""

import os
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
    EMAIL: str = os.environ.get("CHARTAPPS_EMAIL") or _user.get("email") or "chartapps.com@gmail.com"
    PASSWORD: str = os.environ.get("CHARTAPPS_PASSWORD") or _user.get("password") or "YellowBr!ck!23"
