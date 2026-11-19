"""Automated Email Notifier for Playwright Regression Test Runs.

Sends comprehensive HTML email notifications with:
- Vibrant Green (Pass) and Red (Fail) status indicators
- Step-by-step test execution log
- Embedded inline screenshot and attachment of the failed page area on failure
- Run statistics, duration, and GitHub Actions workflow links
"""

import os
import sys
import smtplib
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime


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

                for failure in suite.iter("failure"):
                    failure_details.append({
                        "message": failure.attrib.get("message", "Test assertion failed"),
                        "trace": (failure.text or "").strip()[-1200:],
                    })
                for error in suite.iter("error"):
                    failure_details.append({
                        "message": error.attrib.get("message", "Execution error"),
                        "trace": (error.text or "").strip()[-1200:],
                    })
        except Exception as e:
            print(f"[WARNING] Could not parse junit XML: {e}")

    # Parse step records
    step_records = []
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                step_records = data.get("steps", [])
                if not time_taken or time_taken == "0.0":
                    time_taken = str(data.get("elapsed", "0.0"))
                if failures_count == 0 and data.get("failed_count", 0) > 0:
                    failures_count = data.get("failed_count")
        except Exception as e:
            print(f"[WARNING] Could not parse step json: {e}")

    is_passed = (failures_count == 0 and errors_count == 0)
    return {
        "is_passed": is_passed,
        "total": total_tests,
        "failures": failures_count,
        "errors": errors_count,
        "duration": time_taken,
        "failure_details": failure_details,
        "steps": step_records,
    }


def find_screenshots() -> list[Path]:
    """Find all failure screenshot images in reports directory."""
    screenshots_dir = Path("reports/screenshots")
    if not screenshots_dir.exists():
        return []
    # Return png files sorted newest first
    pngs = sorted(screenshots_dir.glob("*.png"), key=os.path.getmtime, reverse=True)
    return pngs


def build_email_html(results: dict, git_info: dict, screenshot_cid: str = "") -> str:
    """Generate high-impact HTML email body with green/red theme and step indicators."""
    is_passed = results["is_passed"]
    status_text = "PASSED" if is_passed else "FAILED"
    header_color = "#10b981" if is_passed else "#ef4444"
    header_gradient = "linear-gradient(135deg, #059669, #10b981)" if is_passed else "linear-gradient(135deg, #b91c1c, #ef4444)"
    badge_bg = "#dcfce7" if is_passed else "#fee2e2"
    badge_text_color = "#15803d" if is_passed else "#b91c1c"
    badge_icon = "✔" if is_passed else "✖"

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Step rows HTML
    steps_html = ""
    if results["steps"]:
        steps_rows = []
        for s in results["steps"]:
            s_num = s.get("step", 0)
            s_desc = s.get("desc", "")
            s_status = s.get("status", "PASSED")
            s_passed = s_status == "PASSED"
            row_badge_bg = "#ecfdf5" if s_passed else "#fef2f2"
            row_badge_color = "#047857" if s_passed else "#dc2626"
            row_icon = "🟢 Passed" if s_passed else "🔴 Failed"
            steps_rows.append(f"""
            <tr style="border-bottom: 1px solid #e5e7eb;">
              <td style="padding: 10px 14px; font-weight: 600; color: #374151;">Step {s_num:02d}</td>
              <td style="padding: 10px 14px; color: #4b5563; font-size: 14px;">{s_desc}</td>
              <td style="padding: 10px 14px; text-align: right;">
                <span style="display: inline-block; padding: 4px 10px; border-radius: 9999px; font-size: 12px; font-weight: 600; background-color: {row_badge_bg}; color: {row_badge_color};">
                  {row_icon}
                </span>
              </td>
            </tr>
            """)
        steps_html = f"""
        <div style="margin-top: 24px;">
          <h3 style="margin: 0 0 12px; font-size: 16px; color: #1f2937;">📋 Step-by-Step Execution Breakdown</h3>
          <table style="width: 100%; border-collapse: collapse; background: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden;">
            <thead>
              <tr style="background: #f9fafb; border-bottom: 2px solid #e5e7eb; text-align: left; font-size: 13px; color: #6b7280;">
                <th style="padding: 10px 14px;">STEP</th>
                <th style="padding: 10px 14px;">ACTION / ASSERTION</th>
                <th style="padding: 10px 14px; text-align: right;">STATUS</th>
              </tr>
            </thead>
            <tbody>
              {''.join(steps_rows)}
            </tbody>
          </table>
        </div>
        """

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
        <div style="margin-top: 24px; padding: 16px; background: #ffffff; border: 2px solid #f87171; border-radius: 8px;">
          <h3 style="margin: 0 0 8px; font-size: 16px; color: #b91c1c;">📸 Failure Area Screenshot</h3>
          <p style="margin: 0 0 12px; color: #6b7280; font-size: 13px;">Captured visual state of the application when the failure occurred:</p>
          <div style="text-align: center;">
            <img src="cid:{screenshot_cid}" alt="Failure Area Screenshot" style="max-width: 100%; height: auto; border-radius: 6px; border: 1px solid #e5e7eb; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);" />
          </div>
          <p style="margin: 8px 0 0; color: #9ca3af; font-size: 11px; text-align: center;">Image is also attached to this email for full-resolution review.</p>
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
      <div style="max-width: 720px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05); border: 1px solid #e5e7eb;">
        
        <!-- Header Banner -->
        <div style="background: {header_gradient}; padding: 28px 24px; text-align: center; color: #ffffff;">
          <div style="display: inline-block; padding: 6px 14px; background: {badge_bg}; color: {badge_text_color}; font-weight: 800; font-size: 13px; border-radius: 9999px; letter-spacing: 1px; margin-bottom: 10px;">
            {badge_icon} {status_text}
          </div>
          <h1 style="margin: 0; font-size: 24px; font-weight: 700; color: #ffffff;">ChartApps Regression Suite</h1>
          <p style="margin: 6px 0 0; font-size: 14px; opacity: 0.9;">Team Tracker Form Submission & Spreadsheet Verification</p>
        </div>

        <div style="padding: 24px;">
          <!-- Execution Stats Summary -->
          <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 20px;">
            <div style="background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 14px; text-align: center;">
              <div style="font-size: 11px; font-weight: 700; color: #6b7280; text-transform: uppercase;">Result</div>
              <div style="font-size: 18px; font-weight: 800; color: {header_color}; margin-top: 4px;">{status_text}</div>
            </div>
            <div style="background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 14px; text-align: center;">
              <div style="font-size: 11px; font-weight: 700; color: #6b7280; text-transform: uppercase;">Duration</div>
              <div style="font-size: 18px; font-weight: 800; color: #1f2937; margin-top: 4px;">{results['duration']}s</div>
            </div>
            <div style="background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 14px; text-align: center;">
              <div style="font-size: 11px; font-weight: 700; color: #6b7280; text-transform: uppercase;">Trigger</div>
              <div style="font-size: 18px; font-weight: 800; color: #1f2937; margin-top: 4px;">{git_info['event'].capitalize()}</div>
            </div>
          </div>

          <!-- Run Metadata -->
          <table style="width: 100%; border-collapse: collapse; font-size: 13px; color: #4b5563; background: #fdfdfd; border: 1px solid #e5e7eb; border-radius: 6px; padding: 8px;">
            <tr>
              <td style="padding: 6px 12px; font-weight: 600; width: 140px; color: #6b7280;">Repository:</td>
              <td style="padding: 6px 12px;">{git_info['repo']}</td>
            </tr>
            <tr style="background: #f9fafb;">
              <td style="padding: 6px 12px; font-weight: 600; color: #6b7280;">Branch / Commit:</td>
              <td style="padding: 6px 12px;"><code>{git_info['branch']}</code> ({git_info['commit_sha']})</td>
            </tr>
            <tr>
              <td style="padding: 6px 12px; font-weight: 600; color: #6b7280;">Executed At:</td>
              <td style="padding: 6px 12px;">{now_str} (IST: UTC+5:30)</td>
            </tr>
            <tr style="background: #f9fafb;">
              <td style="padding: 6px 12px; font-weight: 600; color: #6b7280;">GitHub Run:</td>
              <td style="padding: 6px 12px;"><a href="{git_info['run_url']}" style="color: #2563eb; text-decoration: none; font-weight: 600;">View Run in GitHub Actions &rarr;</a></td>
            </tr>
          </table>

          {failure_html}
          {screenshot_html}
          {steps_html}

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
    # Read SMTP credentials
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
    screenshots = find_screenshots()

    is_passed = results["is_passed"]
    subject_status = "PASS" if is_passed else "FAIL"
    subject_icon = "🟢" if is_passed else "🔴"
    subject = f"{subject_icon} [{subject_status}] ChartApps Regression Suite Run - {git_info['branch']} ({results['duration']}s)"

    print("=" * 65)
    print(f"[EMAIL] Test Result Status: {subject_status}")
    print(f"[EMAIL] Found {len(screenshots)} failure screenshot(s)")
    print("=" * 65)

    if not smtp_user or not smtp_pass:
        print("[NOTICE] Email credentials (EMAIL_USERNAME / EMAIL_PASSWORD) are not configured in GitHub Secrets.")
        print("[NOTICE] To enable email alerts, add repository secrets:")
        print("         1. EMAIL_USERNAME : Your email address (e.g. chartapps.com@gmail.com)")
        print("         2. EMAIL_PASSWORD : Your Gmail App Password (16 characters)")
        print("         3. EMAIL_TO       : Destination email(s) (optional, defaults to EMAIL_USERNAME)")
        print("[NOTICE] Skipping email delivery for this run.")
        return

    recipients = [e.strip() for e in email_to.split(",") if e.strip()]
    if not recipients:
        print("[WARNING] No recipients specified. Skipping email.")
        return

    # Build MIMEMultipart message
    msg = MIMEMultipart("related")
    msg["Subject"] = subject
    msg["From"] = f"ChartApps CI/CD <{smtp_user}>"
    msg["To"] = ", ".join(recipients)

    screenshot_cid = "failure_screenshot" if (not is_passed and screenshots) else ""
    html_content = build_email_html(results, git_info, screenshot_cid=screenshot_cid)

    msg_alt = MIMEMultipart("alternative")
    msg.attach(msg_alt)
    msg_alt.attach(MIMEText(html_content, "html", "utf-8"))

    # Attach & embed screenshot if failed
    if not is_passed and screenshots:
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

        # Also attach all screenshots as downloadable files
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

    # Dispatch via SMTP
    try:
        print(f"[INFO] Connecting to SMTP server {smtp_server}:{smtp_port}...")
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, recipients, msg.as_string())
        server.quit()
        print(f"[SUCCESS] Email alert sent successfully to: {', '.join(recipients)}")
    except Exception as e:
        print(f"[ERROR] Failed to send email via SMTP: {e}")


if __name__ == "__main__":
    send_notification()
