from __future__ import annotations

import base64
import json
import os
from pathlib import Path

import requests


GITHUB_API = "https://api.github.com"

REPO_OWNER = os.environ.get("GITHUB_OWNER")
REPO_NAME = os.environ.get("GITHUB_REPO")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")


def validate_configuration() -> None:
    missing = []

    if not REPO_OWNER:
        missing.append("GITHUB_OWNER")

    if not REPO_NAME:
        missing.append("GITHUB_REPO")

    if not GITHUB_TOKEN:
        missing.append("GITHUB_TOKEN")

    if missing:
        raise RuntimeError(
            "Missing environment variables: "
            + ", ".join(missing)
        )


def upload_file(
    local_file: str,
    github_path: str,
    commit_message: str,
) -> dict:

    validate_configuration()

    file_path = Path(local_file)

    if not file_path.exists():
        raise FileNotFoundError(
            f"Local file not found: {file_path}"
        )

    content = file_path.read_bytes()

    encoded_content = base64.b64encode(content).decode("utf-8")

    url = (
        f"{GITHUB_API}/repos/"
        f"{REPO_OWNER}/{REPO_NAME}/contents/"
        f"{github_path}"
    )

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    payload = {
        "message": commit_message,
        "content": encoded_content,
    }

    response = requests.put(
        url,
        headers=headers,
        json=payload,
        timeout=30,
    )

    if response.status_code not in (200, 201):
        raise RuntimeError(
            "GitHub API request failed.\n"
            f"Status : {response.status_code}\n"
            f"Response: {response.text}"
        )

    return response.json()


def main() -> None:

    import argparse

    parser = argparse.ArgumentParser(
        description="Upload a file to GitHub repository."
    )

    parser.add_argument(
        "local_file",
        help="Local file to upload.",
    )

    parser.add_argument(
        "github_path",
        help="Destination path inside GitHub repository.",
    )

    parser.add_argument(
        "--message",
        default="chore: upload experiment record",
        help="Git commit message.",
    )

    args = parser.parse_args()

    result = upload_file(
        local_file=args.local_file,
        github_path=args.github_path,
        commit_message=args.message,
    )

    print("Upload successful.")
    print(f"Commit: {result['commit']['html_url']}")
    print(f"Path  : {result['content']['path']}")


if __name__ == "__main__":
    main()
