"""Dynamic test data generator for New App Creation and End-User regression scenarios."""

from datetime import datetime
from typing import Dict


class NewAppTestData:
    """Generates dynamic names, slugs, and form payloads for New App regression testing."""

    @classmethod
    def get_new_app_payload(cls) -> Dict[str, str]:
        """Generate payload for creating a new app, configuring pages, and submitting forms."""
        now = datetime.now()
        date_str = now.strftime("%d-%m-%Y")
        time_tag = now.strftime("%H%M%S")
        date_iso = now.strftime("%Y-%m-%d")
        time_hm = now.strftime("%H:%M")
        time_hms = now.strftime("%H:%M:%S")

        app_name = f"Regression-{date_str}-{time_tag}"
        app_slug = f"regression-{date_str.lower()}-{time_tag}"

        return {
            "app_name": app_name,
            "slug": app_slug,
            "spreadsheet_name": "Regression Testing Automation",
            "sheet_name": "User",
            "col_name": "Name ",
            "col_email": "Email",
            "page_name": "About",
            "page_slug": "about",
            "details_sheet": "Regression Submition",
            "editor_datetime": f"{date_iso} {time_hm}",
            "editor_date": date_iso,
            "editor_text": f"Regression Testing is completed in Editor Mode - {time_hms}",
            "enduser_date": date_iso,
            "enduser_text": f"This is from the end user access form submition - {time_hms}",
        }