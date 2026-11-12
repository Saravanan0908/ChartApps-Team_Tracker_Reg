"""Dynamic test data generator for Team Tracker form submission tests."""

from datetime import datetime
from typing import Dict


class TeamTrackerTestData:
    """Generates dynamic runtime data for Task / Activity form submissions."""

    @staticmethod
    def get_current_date() -> str:
        """Return current date in YYYY-MM-DD format."""
        return datetime.now().strftime("%Y-%m-%d")

    @staticmethod
    def get_current_runtime() -> str:
        """Return current time in HH:MM:SS format."""
        return datetime.now().strftime("%H:%M:%S")

    @classmethod
    def get_form_payload(cls, option: str = "FN") -> Dict[str, str]:
        """Generate form submission data incorporating current date and run time."""
        current_date = cls.get_current_date()
        runtime = cls.get_current_runtime()

        task_desc = f"Testing Task - {current_date} {runtime}"
        activity_desc = f"Automation Script Running - {runtime}"

        return {
            "date": current_date,
            "option": option,
            "task_description": task_desc,
            "activity": activity_desc,
            "runtime": runtime,
        }

