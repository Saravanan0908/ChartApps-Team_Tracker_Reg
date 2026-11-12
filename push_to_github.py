"""Script to push the repository to GitHub using a Personal Access Token (PAT)."""

import os
import sys
import getpass
from pathlib import Path
import dulwich.porcelain as git

REPO_DIR = Path(__file__).resolve().parent
REMOTE_URL = "https://github.com/Saravanan0908/ChartApps-Team_Tracker_Reg.git"


def main():
    print("=" * 65)
    print("Pushing ChartApps Automation Project to GitHub")
    print(f"Target Repository: {REMOTE_URL}")
    print("=" * 65)

    # Check for GITHUB_TOKEN environment variable or prompt user
    token = os.environ.get("GITHUB_TOKEN")
    username = os.environ.get("GITHUB_USER", "Saravanan0908")

    if not token:
        print("\nGitHub requires a Personal Access Token (PAT) to authorize pushes.")
        print("(Generate one at: https://github.com/settings/tokens with 'repo' scope)\n")
        username = input(f"GitHub Username [{username}]: ").strip() or username
        token = getpass.getpass("Enter your GitHub Personal Access Token: ").strip()

    if not token:
        print("[ERROR] Token cannot be empty. Push aborted.")
        sys.exit(1)

    # Format authenticated URL
    auth_url = f"https://{username}:{token}@github.com/Saravanan0908/ChartApps-Team_Tracker_Reg.git"

    print("\nPushing main branch to GitHub...")
    try:
        git.push(str(REPO_DIR), auth_url, "HEAD:refs/heads/main")
        print("\n" + "=" * 65)
        print("[SUCCESS] Project pushed successfully to GitHub!")
        print(f"View your repository at: https://github.com/Saravanan0908/ChartApps-Team_Tracker_Reg")
        print("=" * 65)
    except Exception as e:
        print(f"\n[ERROR] Push failed: {e}")
        print("Please verify that your Personal Access Token has write permissions ('repo' scope).")


if __name__ == "__main__":
    main()
