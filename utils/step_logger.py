"""Step logger utility for live execution indicators in terminal and GitHub Actions."""

import os
import sys
import time
from datetime import datetime

# Reconfigure stdout/stderr to UTF-8 to prevent cp1252 UnicodeEncodeError on Windows CI
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def safe_print(*args, **kwargs):
    """Print to console with encoding fallback for Windows code pages."""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        try:
            encoding = getattr(sys.stdout, "encoding", "ascii") or "ascii"
            clean_args = [
                str(arg).encode(encoding, errors="replace").decode(encoding)
                for arg in args
            ]
            print(*clean_args, **kwargs)
        except Exception:
            pass


class StepLogger:
    """Logs clear, real-time step indicators to stdout and appends to GitHub Step Summary."""

    def __init__(self, suite_name: str = "Team Tracker Regression", total_steps: int = 11):
        self.suite_name = suite_name
        self.total_steps = total_steps
        self.steps_record = []
        self._start_time = time.time()

    def start_suite(self) -> None:
        """Print suite banner at start."""
        safe_print(f"\n{'=' * 75}", flush=True)
        safe_print(f"[START] STARTING TEST SUITE: {self.suite_name} ({self.total_steps} Total Steps)", flush=True)
        safe_print(f"[TIME]  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
        safe_print(f"{'=' * 75}\n", flush=True)

    def step(self, step_num: int, title: str, details: str = "") -> None:
        """Log the start of a test step."""
        now_str = datetime.now().strftime("%H:%M:%S")
        prefix = f"[{now_str}] >> [STEP {step_num:02d}/{self.total_steps:02d}]"
        safe_print(f"\n{prefix} {title}", flush=True)
        if details:
            safe_print(f"               * {details}", flush=True)

    def passed(self, step_num: int, message: str = "") -> None:
        """Log the successful completion of a test step."""
        now_str = datetime.now().strftime("%H:%M:%S")
        msg = f" - {message}" if message else ""
        safe_print(f"[{now_str}] [PASS] [STEP {step_num:02d}/{self.total_steps:02d}]{msg}", flush=True)
        self.steps_record.append((step_num, message or f"Step {step_num} completed", "PASSED"))

    def failed(self, step_num: int, error_msg: str = "") -> None:
        """Log the failure of a test step."""
        now_str = datetime.now().strftime("%H:%M:%S")
        safe_print(f"[{now_str}] [FAIL] [STEP {step_num:02d}/{self.total_steps:02d}] FAILED: {error_msg}", flush=True)
        self.steps_record.append((step_num, error_msg, "FAILED"))

    def finish_suite(self) -> None:
        """Print completion banner, save step execution json, and write to GitHub Step Summary if in CI."""
        import json
        from pathlib import Path
        elapsed = round(time.time() - self._start_time, 2)
        failed_count = sum(1 for _, _, status in self.steps_record if status == "FAILED")
        passed_count = sum(1 for _, _, status in self.steps_record if status == "PASSED")

        safe_print(f"\n{'=' * 75}", flush=True)
        safe_print(f"[FINISH] TEST SUITE COMPLETED: {self.suite_name}", flush=True)
        safe_print(f"[SUMMARY] {passed_count} Passed | {failed_count} Failed | Elapsed: {elapsed}s", flush=True)
        safe_print(f"{'=' * 75}\n", flush=True)

        # Save step execution record to json for email notification
        try:
            reports_dir = Path("reports")
            reports_dir.mkdir(parents=True, exist_ok=True)
            with open(reports_dir / "step_execution.json", "w", encoding="utf-8") as f:
                json.dump({
                    "suite": self.suite_name,
                    "total_steps": self.total_steps,
                    "elapsed": elapsed,
                    "passed_count": passed_count,
                    "failed_count": failed_count,
                    "steps": [
                        {"step": s[0], "desc": s[1], "status": s[2]}
                        for s in self.steps_record
                    ]
                }, f, indent=2)
        except Exception as e:
            safe_print(f"[WARNING] Could not save step_execution.json: {e}", flush=True)

        self._write_github_summary(elapsed, passed_count, failed_count)

    def _write_github_summary(self, elapsed: float, passed_count: int, failed_count: int) -> None:
        """Write execution steps summary table to $GITHUB_STEP_SUMMARY if running in GitHub Actions."""
        summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
        if not summary_file:
            return

        overall_badge = "✅ **PASSED**" if failed_count == 0 else "❌ **FAILED**"
        total_executed = len(self.steps_record)

        lines = [
            f"## 📋 {self.suite_name} - Step Execution Report",
            "",
            f"- **Result**: {overall_badge}",
            f"- **Steps Completed**: `{total_executed}/{self.total_steps}`",
            f"- **Total Duration**: `{elapsed}s`",
            f"- **Execution Time**: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`",
            "",
            "### 🔍 Detailed Step-by-Step Breakdown",
            "",
            "| Step | Action & Description | Status |",
            "| :---: | :--- | :---: |",
        ]

        for num, desc, status in self.steps_record:
            icon = "✅ Passed" if status == "PASSED" else "❌ Failed"
            lines.append(f"| **Step {num:02d}** | {desc} | {icon} |")

        lines.append("")
        try:
            with open(summary_file, "a", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
        except Exception as e:
            safe_print(f"[WARNING] Could not write to GITHUB_STEP_SUMMARY: {e}", flush=True)
