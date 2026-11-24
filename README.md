# ChartApps Playwright Automation Framework (POM)

An enterprise-grade, clean Page Object Model (POM) test automation framework built with **Python**, **Playwright**, and **Pytest**. Features automated session management, dynamic runtime test data, real-time live step streaming, failure screenshot capture, Allure test reporting, and a full GitHub Actions CI/CD pipeline with scheduled auto-execution and email notifications.

---

## 📁 Clean Project Architecture

```plaintext
ChartApps/
├── .github/
│   └── workflows/
│       └── playwright.yml             # GitHub Actions CI/CD (push, PR, cron schedules & manual triggers)
├── constants/
│   ├── urls.py                        # Centralized URLs (Base URL, Dashboard, Auth)
│   └── __init__.py
├── locators/                          # Pure selector definitions (Decoupled from test logic)
│   ├── login_locators.py              # Login & authentication locators
│   ├── spreadsheet_locators.py        # Dashboard & spreadsheet element locators
│   ├── team_tracker_locators.py       # Team Tracker form, inputs, toast, and table locators
│   └── __init__.py
├── pages/                             # Page Object Model Action Classes
│   ├── base_page.py                   # Common Playwright actions (navigate, title, wait, screenshot)
│   ├── login_page.py                  # Login actions and auth completion flows
│   ├── spreadsheet_page.py            # Spreadsheet views and table validations
│   ├── team_tracker_page.py           # Team Tracker actions (auto-login, form submit, datepicker, table verify)
│   └── __init__.py
├── testdata/                          # Test Datasets & Dynamic Generators
│   ├── team_tracker_data.py           # Dynamic date (YYYY-MM-DD) and runtime (HH:MM:SS) generator
│   ├── test_data.py                   # Credential provider (Environment vars -> JSON -> Fallbacks)
│   ├── login_data.example.json        # Example credentials template
│   ├── login_data.json                # Local test credentials (gitignored)
│   └── __init__.py
├── tests/                             # Pytest Test Suites & Fixtures
│   ├── conftest.py                    # Browser fixtures, failure screenshot capture & Allure report hooks
│   ├── setup_auth.py                  # One-time interactive Google login setup utility
│   ├── test_login.py                  # Standalone login verification test
│   ├── test_spreadsheet.py            # Spreadsheet view and session persistence test
│   ├── test_team_tracker_regression.py# Regression suite: Form Submission & Spreadsheet Data Verification
│   └── __init__.py
├── utils/                             # Shared Framework Utilities
│   ├── browser_factory.py             # Browser launcher with persistent contexts & anti-detection args
│   ├── config.py                      # Global runner settings (timeouts, headless toggle, profile paths)
│   ├── email_notifier.py              # HTML email notifier with Pass/Fail status and failure screenshot
│   ├── export_session.py              # Utility to export browser session to storage_state.json for CI
│   ├── step_logger.py                 # Real-time console step logger and GitHub Step Summary generator
│   └── __init__.py
├── reports/                           # Test Reports & Execution Artifacts (Generated automatically)
│   ├── allure-results/                # Allure report test execution results
│   ├── junit_report.xml               # JUnit XML report for test run analytics
│   ├── step_execution.json            # Machine-readable step-by-step test execution record
│   └── screenshots/                   # Screenshots captured automatically on test failure
├── pytest.ini                         # Pytest configuration with test paths, markers & reporting options
├── requirements.txt                   # Framework dependencies
└── README.md                          # Framework documentation
```

---

## 🌟 Key Features & Design Principles

### 1. Page Object Model (POM) Design Pattern
- **Decoupled Responsibilities:**
  - `locators/` defines *where* elements are.
  - `pages/` defines *how* elements interact.
  - `tests/` defines *what* business scenarios to validate.
- **Easy to Understand:** Every function includes comprehensive docstrings, parameter definitions, and step-by-step inline explanations.

### 2. Automated Session & Fallback Authentication
- Cloud CI runners (like GitHub Actions) start fresh without browser cookies.
- When `open_dashboard()` detects an unauthenticated session, it automatically fills credentials from `testdata/test_data.py`, signs in, and caches the session state for the rest of the test execution.

### 3. Dynamic Test Data Generation
- In `testdata/team_tracker_data.py`, tests dynamically inject the current calendar date (`YYYY-MM-DD`) and precise runtime (`HH:MM:SS`), guaranteeing that every execution creates a uniquely verifiable entry.

### 4. Real-time Live Step Streaming
- Tests execute with `StepLogger`, emitting real-time progress indicators:
  ```text
  [12:00:01] >> [STEP 01/11] Open ChartApps Dashboard & Verify Session
  [12:00:04] [PASS] [STEP 01/11] - Dashboard reached and session validated
  ...
  ```
- Pytest runs with `-s -v` and `PYTHONUNBUFFERED=1` so steps appear immediately in the terminal and GitHub Actions logs.
- Summary tables are automatically written to `$GITHUB_STEP_SUMMARY` on GitHub.

### 5. Automated HTML Email Notifications
- At the end of every run, `utils/email_notifier.py`:
  - Sends a **Vibrant Green** email on **PASS** with a complete step breakdown.
  - Sends a **Vibrant Red** email on **FAIL** with error logs and an **embedded inline screenshot** of the failed page area.
  - Sends directly to `saravanans@objectways.com`.

---

## 💻 How to Run Locally

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
playwright install
python -m playwright install chrome
```

---

### 2. Run Commands — Existing App (Scenario 1)

| Method | Command |
|--------|---------|
| Python script | `python tests\test_regression_existing_new_app.py existing` |
| Pytest (Allure) | `pytest -m existing_app -s -v` |
| Batch file | `.\run.bat existing` |
| Debug + Inspector | `.\run_debug_inspect.bat existing` |

---

### 3. Run Commands — New App (Scenario 2)

| Method | Command |
|--------|---------|
| Python script | `python tests\test_regression_existing_new_app.py new` |
| Pytest (Allure) | `pytest -m new_app -s -v` |
| Batch file | `.\run.bat new` |
| Debug + Inspector | `.\run_debug_inspect.bat new` |

---

### 4. Run Commands — Full Suite (Both Scenarios)

| Method | Command |
|--------|---------|
| Python script | `python tests\test_regression_existing_new_app.py all` |
| Pytest (Allure) | `pytest -m regression -s -v` |
| Batch file | `.\run.bat all` or `.\run_pytest.bat regression` |
| Debug + Inspector | `.\run_debug_inspect.bat` |

---

### 5. Codegen / Recorder Mode (Record New Locators)

```powershell
# Opens Playwright Recorder with pre-loaded ChartApps session
.\debug_codegen.bat

# Record on a specific URL
.\debug_codegen.bat https://chartapps.app/dashboard/new-multipage
```

> **PowerShell tip:** Always prefix `.bat` files with `.\` in PowerShell.
> In `cmd.exe` the `.\` prefix is optional.

---

### 6. View Allure Report

```powershell
.\open_allure_report.bat
```

---

## ⚙️ CI/CD & Automated Scheduling (GitHub Actions)

The workflow file is located at [`.github/workflows/playwright.yml`](.github/workflows/playwright.yml).

### Schedule Configuration
```yaml
  schedule:
    # 1. Today's custom run (Nov 19) at 12:45 PM IST (07:15 UTC)
    - cron: '15 7 19 11 *'
    # 2. Daily recurring auto-run at 11:00 AM IST (05:30 UTC)
    - cron: '30 5 * * *'
```

### Triggers Available:
1. **Scheduled Auto-run**: Fires automatically based on the cron schedule.
2. **Manual Run**: Click **"Run workflow"** from the GitHub Actions UI anytime.
3. **Push / Pull Request**: Executes automatically when code is pushed to `main`.
