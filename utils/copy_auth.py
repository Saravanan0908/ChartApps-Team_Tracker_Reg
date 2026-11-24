"""Export .auth_profile/storage_state.json as Base64 and copy to clipboard."""

import base64
import json
import subprocess
import sys
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
AUTH_FILE = BASE_DIR / ".auth_profile" / "storage_state.json"
GITHUB_SECRETS_URL = "https://github.com/Saravanan0908/ChartApps-Team_Tracker_Reg/settings/secrets/actions"


def main() -> None:
    print("=" * 75)
    print(" ChartApps CI/CD Helper: Export Session for GitHub Actions")
    print("=" * 75)

    if not AUTH_FILE.exists():
        print(f"[ERROR] Session file not found at: {AUTH_FILE}")
        print("Please run the regression test locally once first:")
        print("  .\\run.bat")
        sys.exit(1)

    with open(AUTH_FILE, "rb") as f:
        file_bytes = f.read()

    with open(AUTH_FILE, "r", encoding="utf-8") as f:
        state_data = json.load(f)

    cookies = state_data.get("cookies", [])
    total_cookies = len(cookies)
    google_cookies = len([c for c in cookies if "google" in c.get("domain", "")])
    b64_str = base64.b64encode(file_bytes).decode("ascii")

    # Save base64 string to a text file for easy manual copy if clipboard fails
    txt_out = BASE_DIR / "reports" / "auth_storage_state_base64.txt"
    txt_out.parent.mkdir(parents=True, exist_ok=True)
    with open(txt_out, "w", encoding="utf-8") as f:
        f.write(b64_str)

    # Copy to clipboard via Windows clip.exe or PowerShell
    copied = False
    try:
        proc = subprocess.Popen(["clip"], stdin=subprocess.PIPE, text=True)
        proc.communicate(input=b64_str)
        if proc.returncode == 0:
            copied = True
    except Exception:
        pass

    if not copied:
        try:
            proc = subprocess.Popen(
                ["powershell", "-NoProfile", "-Command", "Set-Clipboard -Value $input"],
                stdin=subprocess.PIPE,
                text=True,
            )
            proc.communicate(input=b64_str)
            if proc.returncode == 0:
                copied = True
        except Exception:
            pass

    print(f"\n[INFO] Session loaded from: {AUTH_FILE}")
    print(f"[INFO] Total Cookies: {total_cookies} (including {google_cookies} Google authentication cookies)")
    print(f"[INFO] Encoded Size: {len(b64_str)} characters (fits safely in GitHub Secrets)")

    if copied:
        print("\n" + "=" * 75)
        print(" [SUCCESS] AUTHENTICATED SESSION COPIED TO YOUR CLIPBOARD (Ctrl+V)!")
        print("=" * 75)
    else:
        print("\n[NOTICE] Please copy the Base64 text manually below.")

    print("\nNext Steps (30 seconds):")
    print(f"1. Opening your GitHub Secrets page: {GITHUB_SECRETS_URL}")
    print("2. Click 'New repository secret' (or update 'AUTH_STORAGE_STATE' if already exists)")
    print("3. Name:   AUTH_STORAGE_STATE")
    print("4. Secret: Paste (Ctrl+V) your clipboard")
    print("5. Click 'Add secret' (or 'Update secret')")
    print("=" * 75 + "\n")

    try:
        webbrowser.open(GITHUB_SECRETS_URL)
    except Exception:
        pass


if __name__ == "__main__":
    main()
