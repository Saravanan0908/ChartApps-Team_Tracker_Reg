"""Automated Email Notifier for Playwright Regression Test Runs.

Sends comprehensive HTML email notifications with:
- Vibrant Green (Pass) and Red (Fail) status indicators
- Executive Scenario Checklist Matrix (Existing App vs New App)
- Interactive Step-by-Step Test Execution Checklist with status badges
- Embedded inline screenshot and attachment of the failed page area on failure
- Run statistics, duration, and GitHub Actions workflow links
"""

import os
import sys
import smtplib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

# Ensure project root is in sys.path so 'utils.*' imports work from anywhere
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

try:
    from utils.video_helper import find_videos, trim_video_to_last_n_seconds, clean_passed_videos
except ImportError:
    from video_helper import find_videos, trim_video_to_last_n_seconds, clean_passed_videos


def get_git_info() -> dict:
    """Retrieve run metadata from environment or GitHub Actions."""
    repo = os.environ.get("GITHUB_REPOSITORY", "Saravanan0908/ChartApps-Team_Tracker_Reg")
    server_url = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    run_url = f"{server_url}/{repo}/actions/runs/{run_id}" if run_id else f"{server_url}/{repo}/actions"
    commit_sha = os.environ.get("GITHUB_SHA", "Local")[:7]
    branch = os.environ.get("GITHUB_REF_NAME", "main")
    event = os.environ.get("GITHUB_EVENT_NAME", "manual")
    return {
        "repo": repo,
        "run_url": run_url,
        "commit_sha": commit_sha,
        "branch": branch,
        "event": event,
    }


def parse_test_results() -> dict:
    """Parse junit XML and step execution json to extract test status, timing, and errors."""
    xml_path = Path("reports/junit_report.xml")
    json_path = Path("reports/step_execution.json")

    total_tests = 1
    failures_count = 0
    errors_count = 0
    time_taken = "0.0"
    failure_details = []
    testcases = []

    if xml_path.exists():
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            suite = root if root.tag == "testsuite" else root.find("testsuite")
            if suite is not None:
                total_tests = int(suite.attrib.get("tests", "1"))
                failures_count = int(suite.attrib.get("failures", "0"))
                errors_count = int(suite.attrib.get("errors", "0"))
                time_taken = suite.attrib.get("time", "0.0")

                for tc in suite.iter("testcase"):
                    tc_name = tc.attrib.get("name", "Unknown Test")
                    tc_time = tc.attrib.get("time", "0.0")
                    is_failed = False
                    err_msg = ""
                    for failure in tc.iter("failure"):
                        is_failed = True
                        err_msg = failure.attrib.get("message", "Assertion failed")
                        failure_details.append({
                            "message": f"[{tc_name}] {err_msg}",
                            "trace": (failure.text or "").strip()[-1200:],
                        })
                    for error in tc.iter("error"):
                        is_failed = True
                        err_msg = error.attrib.get("message", "Error")
                        failure_details.append({
                            "message": f"[{tc_name}] {err_msg}",
                            "trace": (error.text or "").strip()[-1200:],
                        })
                    testcases.append({
                        "name": tc_name,
                        "time": tc_time,
                        "passed": not is_failed,
                        "error": err_msg,
                    })
        except Exception as e:
            print(f"[WARNING] Could not parse junit XML: {e}")

    # Parse multi-scenario suites and step records
    step_records = []
    suites_data = []
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                suites_data = data.get("suites", [])
                step_records = data.get("steps", [])
                if not time_taken or time_taken == "0.0":
                    time_taken = str(data.get("elapsed", "0.0"))
                if failures_count == 0 and data.get("failed_count", 0) > 0:
                    failures_count = data.get("failed_count")
        except Exception as e:
            print(f"[WARNING] Could not parse step json: {e}")

    # If no suites in json, create default single suite entry from step_records
    if not suites_data and step_records:
        suites_data = [{
            "suite": "Regression Test",
            "total_steps": len(step_records),
            "passed_count": len([s for s in step_records if s.get("status") == "PASSED"]),
            "failed_count": len([s for s in step_records if s.get("status") != "PASSED"]),
            "steps": step_records,
        }]

    is_passed = (failures_count == 0 and errors_count == 0)
    return {
        "is_passed": is_passed,
        "total": total_tests,
        "failures": failures_count,
        "errors": errors_count,
        "duration": time_taken,
        "failure_details": failure_details,
        "testcases": testcases,
        "suites": suites_data,
        "steps": step_records,
    }


def find_screenshots() -> list[Path]:
    """Find all failure screenshot images in reports directory."""
    screenshots_dir = Path("reports/screenshots")
    if not screenshots_dir.exists():
        return []
    pngs = sorted(screenshots_dir.glob("*.png"), key=os.path.getmtime, reverse=True)
    return pngs


def build_email_html(results: dict, git_info: dict, screenshot_cid: str = "", video_filename: str = "") -> str:
    """Generate high-impact HTML email body with scenario matrix, checklist, video & report links."""
    is_passed = results["is_passed"]
    status_text = "PASSED" if is_passed else "FAILED"
    header_color = "#10b981" if is_passed else "#ef4444"
    header_gradient = "linear-gradient(135deg, #059669, #10b981)" if is_passed else "linear-gradient(135deg, #b91c1c, #ef4444)"
    badge_bg = "#dcfce7" if is_passed else "#fee2e2"
    badge_text_color = "#15803d" if is_passed else "#b91c1c"
    badge_icon = "✔" if is_passed else "✖"

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    run_url = git_info.get("run_url", "https://github.com/Saravanan0908/ChartApps-Team_Tracker_Reg/actions")
    artifacts_url = f"{run_url}#artifacts" if "/runs/" in run_url else run_url

    # 1. Executive Scenario Matrix
    scenario_cards = []
    default_scenarios = [
        {"title": "Scenario 1: Existing App (Team Tracker)", "desc": "Dashboard navigation, dynamic task entry, toast check, spreadsheet storage verification"},
        {"title": "Scenario 2: New App Creation & Workflow", "desc": "App creation, Google OAuth consent, picker sheet, details page, blocks, end-user verification, cleanup"},
    ]

    # Map parsed suites or fallback
    if results["suites"]:
        for idx, suite in enumerate(results["suites"]):
            s_name = suite.get("suite", f"Scenario {idx+1}")
            s_pass = suite.get("failed_count", 0) == 0
            s_color = "#10b981" if s_pass else "#ef4444"
            s_bg = "#ecfdf5" if s_pass else "#fef2f2"
            s_badge = "🟢 PASSED" if s_pass else "🔴 FAILED"
            s_total = suite.get("total_steps", 0)
            s_passed_steps = suite.get("passed_count", 0)

            scenario_cards.append(f"""
            <div style="background: #ffffff; border: 1px solid #e5e7eb; border-left: 4px solid {s_color}; border-radius: 8px; padding: 14px 16px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-size: 14px; font-weight: 700; color: #1f2937;">{s_name}</span>
                <span style="display: inline-block; padding: 3px 10px; border-radius: 9999px; font-size: 12px; font-weight: 700; background: {s_bg}; color: {s_color};">{s_badge}</span>
              </div>
              <div style="font-size: 12px; color: #6b7280;">
                Steps Verified: <strong>{s_passed_steps}/{s_total}</strong> completed successfully
              </div>
            </div>
            """)
    else:
        for idx, sc in enumerate(default_scenarios):
            s_color = "#10b981" if is_passed else "#ef4444"
            s_bg = "#ecfdf5" if is_passed else "#fef2f2"
            s_badge = "🟢 PASSED" if is_passed else "🔴 FAILED"
            scenario_cards.append(f"""
            <div style="background: #ffffff; border: 1px solid #e5e7eb; border-left: 4px solid {s_color}; border-radius: 8px; padding: 14px 16px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-size: 14px; font-weight: 700; color: #1f2937;">{sc['title']}</span>
                <span style="display: inline-block; padding: 3px 10px; border-radius: 9999px; font-size: 12px; font-weight: 700; background: {s_bg}; color: {s_color};">{s_badge}</span>
              </div>
              <div style="font-size: 12px; color: #6b7280;">{sc['desc']}</div>
            </div>
            """)

    scenario_matrix_html = f"""
    <div style="margin-top: 24px;">
      <h3 style="margin: 0 0 12px; font-size: 16px; color: #1f2937;">📑 Regression Scenarios Executive Summary</h3>
      {''.join(scenario_cards)}
    </div>
    """

    # 2. Detailed Checklist HTML per Suite
    checklist_sections = []
    if results["suites"]:
        for suite in results["suites"]:
            s_title = suite.get("suite", "Scenario Checklist")
            s_steps = suite.get("steps", [])
            step_rows = []
            for s in s_steps:
                s_num = s.get("step", 0)
                s_desc = s.get("desc", "")
                s_status = s.get("status", "PASSED")
                s_passed = s_status == "PASSED"
                icon = "✔" if s_passed else "✖"
                badge_bg = "#ecfdf5" if s_passed else "#fef2f2"
                badge_col = "#047857" if s_passed else "#dc2626"
                step_rows.append(f"""
                <tr style="border-bottom: 1px solid #f3f4f6;">
                  <td style="padding: 10px 12px; width: 40px; text-align: center;">
                    <span style="display: inline-block; width: 22px; height: 22px; line-height: 22px; border-radius: 50%; background: {badge_bg}; color: {badge_col}; font-size: 12px; font-weight: 700;">{icon}</span>
                  </td>
                  <td style="padding: 10px 12px; font-weight: 700; color: #4b5563; width: 75px; font-size: 13px;">Step {s_num:02d}</td>
                  <td style="padding: 10px 12px; color: #1f2937; font-size: 13px;">{s_desc}</td>
                  <td style="padding: 10px 12px; text-align: right; width: 90px;">
                    <span style="display: inline-block; padding: 3px 10px; border-radius: 9999px; font-size: 11px; font-weight: 800; background: {badge_bg}; color: {badge_col}; letter-spacing: 0.5px;">
                      {s_status}
                    </span>
                  </td>
                </tr>
                """)
            checklist_sections.append(f"""
            <div style="margin-top: 18px; background: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
              <div style="background: #f9fafb; padding: 12px 16px; border-bottom: 1px solid #e5e7eb; font-weight: 700; font-size: 14px; color: #1f2937;">
                📋 Checklist: {s_title}
              </div>
              <table style="width: 100%; border-collapse: collapse;">
                <thead>
                  <tr style="background: #f3f4f6; text-align: left; font-size: 11px; font-weight: 700; color: #6b7280; text-transform: uppercase;">
                    <th style="padding: 8px 12px; text-align: center; width: 40px;">Status</th>
                    <th style="padding: 8px 12px; width: 75px;">Step</th>
                    <th style="padding: 8px 12px;">Verification Item</th>
                    <th style="padding: 8px 12px; text-align: right; width: 90px;">Result</th>
                  </tr>
                </thead>
                <tbody>
                  {''.join(step_rows)}
                </tbody>
              </table>
            </div>
            """)

    checklist_html = f"""
    <div style="margin-top: 24px;">
      <h3 style="margin: 0 0 12px; font-size: 16px; color: #1f2937;">✅ Scenario Step-by-Step Verification Checklist</h3>
      {''.join(checklist_sections)}
    </div>
    """ if checklist_sections else ""

    # Failure details HTML
    failure_html = ""
    if not is_passed and results["failure_details"]:
        fail_blocks = []
        for f in results["failure_details"]:
            msg = f.get("message", "Failure")
            trace = f.get("trace", "")
            fail_blocks.append(f"""
            <div style="background-color: #fff1f2; border: 1px solid #fecdd3; border-radius: 8px; padding: 14px; margin-bottom: 12px;">
              <div style="font-weight: 700; color: #be123c; font-size: 14px; margin-bottom: 6px;">❌ Error: {msg}</div>
              {f'<pre style="background: #1f2937; color: #f87171; padding: 10px; border-radius: 6px; font-size: 12px; overflow-x: auto; white-space: pre-wrap; font-family: Consolas, monospace; margin: 0;">{trace}</pre>' if trace else ''}
            </div>
            """)
        failure_html = f"""
        <div style="margin-top: 24px;">
          <h3 style="margin: 0 0 12px; font-size: 16px; color: #be123c;">⚠️ Failure Analysis & Log</h3>
          {''.join(fail_blocks)}
        </div>
        """

    # Screenshot HTML
    screenshot_html = ""
    if not is_passed and screenshot_cid:
        screenshot_html = f"""
        <div style="margin-top: 24px; padding: 18px; background: #ffffff; border: 2px solid #ef4444; border-radius: 8px; box-shadow: 0 2px 4px rgba(239,68,68,0.1);">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <h3 style="margin: 0; font-size: 16px; color: #b91c1c;">📸 Failure Area Screenshot</h3>
            <a href="{artifacts_url}" target="_blank" style="font-size: 12px; font-weight: 700; color: #ef4444; text-decoration: none;">View in Artifacts &rarr;</a>
          </div>
          <p style="margin: 0 0 14px; color: #6b7280; font-size: 13px;">Captured visual state of the application at the exact point of test failure:</p>
          <div style="text-align: center;">
            <img src="cid:{screenshot_cid}" alt="Failure Area Screenshot" style="max-width: 100%; height: auto; border-radius: 6px; border: 1px solid #e5e7eb; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);" />
          </div>
          <p style="margin: 10px 0 0; color: #6b7280; font-size: 12px; text-align: center;">Attached to this email as a high-resolution PNG image file.</p>
        </div>
        """

    # Video HTML (only on failure when video is attached)
    video_html = ""
    if not is_passed:
        vid_title = f"🎥 Last 20s Failure Video ({video_filename})" if video_filename else "🎥 Test Execution Video Artifacts"
        vid_desc = f"A 20-second video recording capturing the browser actions directly leading up to the failure (<code>{video_filename}</code>) has been attached to this email and archived in GitHub Actions artifacts." if video_filename else "Test execution video recording has been captured and archived in the GitHub Actions artifacts repository."
        video_html = f"""
        <div style="margin-top: 20px; padding: 16px 18px; background: #fff1f2; border: 1px solid #fecdd3; border-left: 4px solid #ef4444; border-radius: 8px;">
          <div style="font-weight: 700; color: #be123c; font-size: 15px; margin-bottom: 6px;">{vid_title}</div>
          <p style="margin: 0 0 12px; font-size: 13px; color: #4b5563;">{vid_desc}</p>
          <div>
            <a href="{artifacts_url}" target="_blank" style="display: inline-block; padding: 8px 16px; background: #dc2626; color: #ffffff; text-decoration: none; border-radius: 6px; font-size: 12px; font-weight: 700;">
              🎥 Download Failure Video & Run Artifacts
            </a>
          </div>
        </div>
        """
    else:
        video_html = f"""
        <div style="margin-top: 20px; padding: 16px 18px; background: #ecfdf5; border: 1px solid #a7f3d0; border-left: 4px solid #10b981; border-radius: 8px;">
          <div style="font-weight: 700; color: #065f46; font-size: 15px; margin-bottom: 4px;">🎉 All Regression Checks Succeeded</div>
          <div style="font-size: 13px; color: #047857;">
            All assertion checkpoints across Scenario 1 (Team Tracker) passed without errors. Video recording and failure screenshots were automatically cleaned up to keep email size minimal. Full report logs and Allure artifacts are accessible via the links below.
          </div>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Test Execution: {status_text}</title>
    </head>
    <body style="margin: 0; padding: 20px; background-color: #f3f4f6; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1f2937;">
      <div style="max-width: 760px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05); border: 1px solid #e5e7eb;">
        
        <!-- Header Banner -->
        <div style="background: {header_gradient}; padding: 28px 24px; text-align: center; color: #ffffff;">
          <div style="display: inline-block; padding: 6px 14px; background: {badge_bg}; color: {badge_text_color}; font-weight: 800; font-size: 13px; border-radius: 9999px; letter-spacing: 1px; margin-bottom: 10px;">
            {badge_icon} {status_text}
          </div>
          <h1 style="margin: 0; font-size: 24px; font-weight: 700; color: #ffffff;">ChartApps Regression Suite</h1>
          <p style="margin: 6px 0 0; font-size: 14px; opacity: 0.95;">Existing App (Team Tracker) & New App Creation Workflows</p>
        </div>

        <div style="padding: 24px;">
          <!-- Execution Stats Summary -->
          <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 20px;">
            <div style="background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px; text-align: center;">
              <div style="font-size: 11px; font-weight: 700; color: #6b7280; text-transform: uppercase;">Result</div>
              <div style="font-size: 16px; font-weight: 800; color: {header_color}; margin-top: 4px;">{status_text}</div>
            </div>
            <div style="background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px; text-align: center;">
              <div style="font-size: 11px; font-weight: 700; color: #6b7280; text-transform: uppercase;">Duration</div>
              <div style="font-size: 16px; font-weight: 800; color: #1f2937; margin-top: 4px;">{results['duration']}s</div>
            </div>
            <div style="background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px; text-align: center;">
              <div style="font-size: 11px; font-weight: 700; color: #6b7280; text-transform: uppercase;">Scenarios</div>
              <div style="font-size: 16px; font-weight: 800; color: #1f2937; margin-top: 4px;">{len(results['suites']) or 1} Test(s)</div>
            </div>
            <div style="background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px; text-align: center;">
              <div style="font-size: 11px; font-weight: 700; color: #6b7280; text-transform: uppercase;">Trigger</div>
              <div style="font-size: 16px; font-weight: 800; color: #1f2937; margin-top: 4px;">{git_info['event'].capitalize()}</div>
            </div>
          </div>

          <!-- Quick Action Buttons: Allure & Artifacts -->
          <div style="text-align: center; margin-bottom: 22px;">
            <a href="{run_url}" target="_blank" style="display: inline-block; background: #2563eb; color: #ffffff; padding: 11px 20px; margin: 4px 6px; border-radius: 8px; text-decoration: none; font-weight: 700; font-size: 13px; box-shadow: 0 2px 4px rgba(37,99,235,0.25);">
              📊 View Full Test & Allure Report
            </a>
            <a href="{artifacts_url}" target="_blank" style="display: inline-block; background: #4b5563; color: #ffffff; padding: 11px 20px; margin: 4px 6px; border-radius: 8px; text-decoration: none; font-weight: 700; font-size: 13px; box-shadow: 0 2px 4px rgba(0,0,0,0.12);">
              📦 Download Allure & Video Artifacts
            </a>
          </div>

          <!-- Run Metadata & Schedule Information -->
          <table style="width: 100%; border-collapse: collapse; font-size: 13px; color: #4b5563; background: #fdfdfd; border: 1px solid #e5e7eb; border-radius: 8px; padding: 8px; margin-bottom: 20px;">
            <tr>
              <td style="padding: 8px 12px; font-weight: 600; width: 160px; color: #6b7280;">Repository:</td>
              <td style="padding: 8px 12px;">{git_info['repo']}</td>
            </tr>
            <tr style="background: #f9fafb;">
              <td style="padding: 8px 12px; font-weight: 600; color: #6b7280;">Branch / Commit:</td>
              <td style="padding: 8px 12px;"><code>{git_info['branch']}</code> ({git_info['commit_sha']})</td>
            </tr>
            <tr>
              <td style="padding: 8px 12px; font-weight: 600; color: #6b7280;">Executed At:</td>
              <td style="padding: 8px 12px;">{now_str} IST (Asia/Kolkata)</td>
            </tr>
            <tr style="background: #f9fafb;">
              <td style="padding: 8px 12px; font-weight: 600; color: #6b7280;">Daily Auto-Schedule:</td>
              <td style="padding: 8px 12px;">⏰ <strong>11:00 AM IST & 6:00 PM IST</strong> (05:30 & 12:30 UTC)</td>
            </tr>
            <tr>
              <td style="padding: 8px 12px; font-weight: 600; color: #6b7280;">Allure Report Link:</td>
              <td style="padding: 8px 12px;"><a href="{run_url}" target="_blank" style="color: #2563eb; text-decoration: none; font-weight: 600;">Open GitHub Run & Allure Report &rarr;</a></td>
            </tr>
            <tr style="background: #f9fafb;">
              <td style="padding: 8px 12px; font-weight: 600; color: #6b7280;">Video & Artifacts Link:</td>
              <td style="padding: 8px 12px;"><a href="{artifacts_url}" target="_blank" style="color: #2563eb; text-decoration: none; font-weight: 600;">Download Videos, Screenshots & Allure Results &rarr;</a></td>
            </tr>
          </table>

          {scenario_matrix_html}
          {failure_html}
          {screenshot_html}
          {video_html}
          {checklist_html}

          <div style="margin-top: 28px; padding-top: 16px; border-top: 1px solid #e5e7eb; text-align: center; color: #9ca3af; font-size: 12px;">
            Automated regression alert powered by Playwright & GitHub Actions CI/CD.
          </div>
        </div>
      </div>
    </body>
    </html>
    """
    return html


def send_notification() -> None:
    """Main dispatch function to assemble and send email."""
    smtp_user = os.environ.get("EMAIL_USERNAME") or os.environ.get("SMTP_USER") or ""
    smtp_pass = os.environ.get("EMAIL_PASSWORD") or os.environ.get("SMTP_PASS") or ""
    email_to = os.environ.get("EMAIL_TO") or "saravanans@objectways.com"
    smtp_server = os.environ.get("SMTP_SERVER") or "smtp.gmail.com"
    raw_port = os.environ.get("SMTP_PORT") or "587"
    try:
        smtp_port = int(raw_port)
    except Exception:
        smtp_port = 587

    results = parse_test_results()
    git_info = get_git_info()
    is_passed = results["is_passed"]

    screenshots = find_screenshots() if not is_passed else []
    videos = find_videos() if not is_passed else []
    video_to_attach = None
    if not is_passed and videos:
        # Trim latest video to last 20 seconds
        video_to_attach = trim_video_to_last_n_seconds(videos[0], max_seconds=20)
    elif is_passed:
        # Clean up video files on pass
        clean_passed_videos()

    subject_status = "PASS" if is_passed else "FAIL"
    subject_icon = "🟢" if is_passed else "🔴"
    subject = f"{subject_icon} [{subject_status}] ChartApps Regression Suite (Existing & New App) - {git_info['branch']} ({results['duration']}s)"

    print("=" * 65)
    print(f"[EMAIL] Test Result Status: {subject_status}")
    if not is_passed:
        print(f"[EMAIL] Found {len(screenshots)} failure screenshot(s)")
        print(f"[EMAIL] Failure video attached: {video_to_attach.name if video_to_attach else 'None'}")
    else:
        print(f"[EMAIL] All tests PASSED! Video/screenshot attachments suppressed; checklist report generated.")
    print("=" * 65)

    if not smtp_user or not smtp_pass:
        print("[NOTICE] Email credentials (EMAIL_USERNAME / EMAIL_PASSWORD) are not configured in environment.")
        print("[NOTICE] Skipping email delivery for this run.")
        return

    recipients = [e.strip() for e in email_to.split(",") if e.strip()]
    if not recipients:
        print("[WARNING] No recipients specified. Skipping email.")
        return

    msg = MIMEMultipart("related")
    msg["Subject"] = subject
    msg["From"] = f"ChartApps CI/CD <{smtp_user}>"
    msg["To"] = ", ".join(recipients)

    screenshot_cid = "failure_screenshot" if (not is_passed and screenshots) else ""
    video_filename = video_to_attach.name if (not is_passed and video_to_attach) else ""
    html_content = build_email_html(results, git_info, screenshot_cid=screenshot_cid, video_filename=video_filename)

    msg_alt = MIMEMultipart("alternative")
    msg.attach(msg_alt)
    msg_alt.attach(MIMEText(html_content, "html", "utf-8"))

    # ONLY attach screenshot and video IF FAILED
    if not is_passed:
        if screenshots:
            primary_screenshot = screenshots[0]
            try:
                with open(primary_screenshot, "rb") as img_f:
                    img_data = img_f.read()
                    img = MIMEImage(img_data)
                    img.add_header("Content-ID", f"<{screenshot_cid}>")
                    img.add_header("Content-Disposition", "inline", filename=primary_screenshot.name)
                    msg.attach(img)
                    print(f"[INFO] Embedded inline screenshot: {primary_screenshot.name}")
            except Exception as e:
                print(f"[WARNING] Could not embed screenshot {primary_screenshot}: {e}")

            for sc in screenshots:
                try:
                    with open(sc, "rb") as sc_file:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(sc_file.read())
                        encoders.encode_base64(part)
                        part.add_header("Content-Disposition", f'attachment; filename="{sc.name}"')
                        msg.attach(part)
                        print(f"[INFO] Attached screenshot file: {sc.name}")
                except Exception as e:
                    print(f"[WARNING] Could not attach screenshot {sc}: {e}")

        if video_to_attach and video_to_attach.exists():
            try:
                with open(video_to_attach, "rb") as vid_file:
                    v_mime = "video/mp4" if video_to_attach.suffix == ".mp4" else "video/webm"
                    main_t, sub_t = v_mime.split("/")
                    part = MIMEBase(main_t, sub_t)
                    part.set_payload(vid_file.read())
                    encoders.encode_base64(part)
                    part.add_header("Content-Disposition", f'attachment; filename="failure_run_last20s{video_to_attach.suffix}"')
                    msg.attach(part)
                    print(f"[INFO] Attached last 20s failure video: {video_to_attach.name}")
            except Exception as e:
                print(f"[WARNING] Could not attach failure video {video_to_attach}: {e}")


if __name__ == "__main__":
    send_notification()
