# ChartApps Playwright Automation Framework (POM)

A robust, enterprise-grade test automation framework built with **Python**, **Playwright**, and **Pytest** following the **Page Object Model (POM)** design pattern. It includes Google OAuth bot-detection bypass, dynamic runtime test data, scenario-level failure capture, and **Azure DevOps HTML & JUnit reporting**.

---

## 📁 Project Architecture

```plaintext
ChartApps/
├── constants/                         # Application routes and global constants
│   ├── urls.py                        # Base URLs, auth, and dashboard routes
│   └── __init__.py
├── locators/                          # UI element locators separated from page logic
│   ├── login_locators.py              # Login & Google OAuth locators
│   ├── spreadsheet_locators.py        # Dashboard & spreadsheet element locators
│   ├── team_tracker_locators.py       # Team Tracker form, inputs, toast & table locators
│   └── __init__.py
├── pages/                             # Page Object Model action classes
│   ├── base_page.py                   # Common Playwright interactions (navigate, url, title)
│   ├── login_page.py                  # Login actions, Google auth & completion detection
│   ├── spreadsheet_page.py            # Spreadsheet views, table validation, and session checks
│   ├── team_tracker_page.py           # Team Tracker form submission, datepicker & table verify
│   └── __init__.py
├── testdata/                          # Test datasets and dynamic generators
│   ├── login_data.json                # User credentials configuration
│   ├── test_data.py                   # Data loader for login tests
│   ├── team_tracker_data.py           # Dynamic current date (YYYY-MM-DD) and run time generator
│   └── __init__.py
├── utils/                             # Shared utilities and browser context management
│   ├── browser_factory.py             # Persistent Chrome launcher with anti-detection flags
│   ├── config.py                      # Global timeout, channel, and profile directory configs
│   └── __init__.py
├── tests/                             # Test suites and fixtures
│   ├── conftest.py                    # Pytest fixtures + automatic failure screenshot hook
│   ├── setup_auth.py                  # One-time Google login setup script
│   ├── test_login.py                  # Google login flow test
│   ├── test_spreadsheet.py            # Session reuse & spreadsheet validation test
│   ├── test_team_tracker_regression.py # Regression test for Form Submission & Data Stored
│   └── __init__.py
├── reports/                           # Test execution reports and screenshots (auto-generated)
│   ├── azure_test_report.html         # Self-contained Azure-ready HTML dashboard
│   ├── junit_report.xml               # JUnit XML for Azure DevOps PublishTestResults task
│   └── screenshots/                   # Scenario-level screenshots captured upon test failure
├── .auth_profile/                     # Persistent Chrome profile retaining Google authentication
├── pytest.ini                         # Pytest configuration with Azure reporting & markers
├── record.py                          # Codegen runner with Google Anti-Bot bypass
├── start_login.bat                    # One-click native Chrome launcher for manual login
├── record_codegen.bat                 # One-click Playwright Codegen attacher (port 9222)
├── requirements.txt                   # Framework dependencies
└── README.md                          # Comprehensive documentation
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites & Installation
Ensure you have Python 3.10+ and Google Chrome installed. Install dependencies:
```powershell
pip install -r requirements.txt
playwright install
```

---

## 🔑 Handling Google Authentication (Anti-Bot Bypass)

Google blocks automated browsers from entering passwords with:
> *"Couldn't sign you in — This browser or app may not be secure."*

This framework provides two proven methods to bypass this block:

### Method A: One-Time Manual Login (Recommended)
1. Run the native Chrome login launcher:
   ```powershell
   .\start_login.bat
   ```
2. Log in with your Google email, password, and 2FA.
3. Once you reach the ChartApps dashboard, keep the browser open or close it. Your profile is automatically saved to `.auth_profile/`.
4. Subsequent test runs will now reuse this profile automatically!

### Method B: Playwright Codegen with Bot-Bypass
If you want to record new tests using Playwright's visual inspector without being blocked by Google:
```powershell
python record.py
```
*This launches the Playwright Inspector on real Google Chrome with the `--enable-automation` flag removed, allowing you to enter your email and password without Google's security block.*

---

## 🧪 Test Execution Commands

| Scenario / Goal | Command | Description |
| :--- | :--- | :--- |
| **Run Regression Suite** | `pytest -m regression` | Runs the Team Tracker form submission and data stored validation. |
| **Run All Tests** | `pytest` | Executes all test suites and generates the Azure HTML & XML reports. |
| **Run Form Submission (Standalone)** | `python tests/test_team_tracker_regression.py` | Runs regression test directly and keeps the browser open for visual inspection. |
| **Run Spreadsheet Operations** | `pytest tests/test_spreadsheet.py -v` | Validates spreadsheet loading using the retained session. |
| **Run Login Test** | `pytest tests/test_login.py -v` | Executes the login test. |
| **Run in Headed Mode** | `pytest --headed` | Displays the browser window during test execution. |

---

## 📊 Azure DevOps Test Reporting & Failure Identification

The framework generates **scenario-level test results** formatted for Azure DevOps pipelines:

### Auto-Generated Reports
1. **Azure HTML Dashboard (`reports/azure_test_report.html`)**:
   - Self-contained single-file HTML report.
   - Shows pass/fail status, execution time, and duration for every individual test scenario.
   - Embeds failure diagnostics directly in the table.
   - **Automatic Browser Launch on Failure**: Whenever a test scenario fails, this report automatically opens in your default web browser for immediate review.
2. **JUnit XML (`reports/junit_report.xml`)**:
   - Machine-readable test execution data natively consumed by Azure DevOps Pipelines.
3. **Automatic Scenario-Level Failure Screenshots (`reports/screenshots/`)**:
   - Whenever any test scenario fails, a hook in `conftest.py` automatically captures the browser page state.
   - The screenshot is linked and embedded directly inside the HTML report next to the failed test step with a `❌ Scenario Failed` label.

### Azure DevOps Pipeline Configuration (`azure-pipelines.yml`)
Add the following steps to your Azure pipeline to display scenario results and the HTML report in Azure DevOps:

```yaml
trigger:
  - main

pool:
  vmImage: 'windows-latest'

steps:
- task: UsePythonVersion@0
  inputs:
    versionSpec: '3.12'
  displayName: 'Use Python 3.12'

- script: |
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    playwright install chromium chrome
  displayName: 'Install Dependencies & Playwright'

- script: |
    pytest -m regression --html=reports/azure_test_report.html --self-contained-html --junitxml=reports/junit_report.xml
  displayName: 'Execute Playwright Regression Tests'

# Publishes Scenario-Level Results in Azure DevOps "Tests" tab
- task: PublishTestResults@2
  inputs:
    testResultsFormat: 'JUnit'
    testResultsFiles: 'reports/junit_report.xml'
    searchFolder: '$(System.DefaultWorkingDirectory)'
    failTaskOnFailedTests: true
    testRunTitle: 'ChartApps Regression Test Results'
  displayName: 'Publish Scenario Test Results'
  condition: always()

# Publishes the interactive HTML Report as a downloadable pipeline artifact
- task: PublishPipelineArtifact@1
  inputs:
    targetPath: 'reports/azure_test_report.html'
    artifact: 'Azure_HTML_Test_Report'
  displayName: 'Publish Azure HTML Test Report'
  condition: always()
```

---

## 🧩 Page Object Model (POM) Design Summary

- **Separation of Concerns**: Locators (`locators/`) are separated from page actions (`pages/`), test data (`testdata/`), and test assertions (`tests/`).
- **Dynamic Date & Time**: `TeamTrackerTestData` injects the exact `YYYY-MM-DD` date and execution timestamp into form fields dynamically to ensure test idempotency.
- **Robust Overlay Handling**: Form submit handles PrimeReact calendar and dropdown overlays with automatic focus clearing and `force=True` fallback.
- **Session Continuity**: Browser contexts maintain cookies and session state across runs, preventing recurring 2FA or OAuth prompts.

