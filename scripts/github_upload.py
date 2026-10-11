"""
Upload satu file ke repository GitHub lewat Contents API.

Bisa dipakai dari Kaggle untuk mengirim file ke SATU atau BEBERAPA branch
sekaligus (mis. Master dan model_history) tanpa error 409/422 "conflict".

Kenapa versi lama error "conflict":
  * Request PUT tidak mengirim `sha` file lama. Kalau file sudah ada di
    GitHub, API menolak dengan 422 ("sha wasn't supplied") atau
    409 Conflict (sha tidak cocok / branch berubah di tengah jalan).
  * Request tidak mengirim `branch`, jadi selalu masuk ke default branch
    (Master) dan tidak pernah bisa menulis ke model_history.

Versi ini:
  * mengambil `sha` file terbaru di branch tujuan sebelum upload,
  * mengirim `branch` secara eksplisit,
  * mengulang (retry) otomatis bila terjadi 409/422 karena sha basi,
  * bisa upload ke beberapa branch: --branch Master --branch model_history

Contoh di Kaggle:
    import os
    from kaggle_secrets import UserSecretsClient
    os.environ["GITHUB_TOKEN"] = UserSecretsClient().get_secret("GITHUB_TOKEN")
    os.environ["GITHUB_OWNER"] = "fatih-collab"
    os.environ["GITHUB_REPO"] = "model-lab"

    !python github_upload.py notebook.ipynb my-notebook.ipynb \
        --branch Master --branch model_history
"""

from __future__ import annotations

import base64
import os
import time
from pathlib import Path
from urllib.parse import quote

import requests


GITHUB_API = "https://api.github.com"

REPO_OWNER = os.environ.get("GITHUB_OWNER")
REPO_NAME = os.environ.get("GITHUB_REPO")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
DEFAULT_BRANCH = os.environ.get("GITHUB_BRANCH")  # opsional

MAX_ATTEMPTS = 5


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


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _contents_url(github_path: str) -> str:
    clean_path = github_path.lstrip("/")
    return (
        f"{GITHUB_API}/repos/"
        f"{REPO_OWNER}/{REPO_NAME}/contents/"
        f"{quote(clean_path)}"
    )


def branch_exists(branch: str) -> bool:
    url = (
        f"{GITHUB_API}/repos/{REPO_OWNER}/{REPO_NAME}"
        f"/branches/{quote(branch, safe='')}"
    )
    response = requests.get(url, headers=_headers(), timeout=30)
    return response.status_code == 200


def get_remote_sha(github_path: str, branch: str | None) -> str | None:
    """Kembalikan sha file di branch tujuan, atau None bila belum ada."""
    params = {"ref": branch} if branch else None

    response = requests.get(
        _contents_url(github_path),
        headers=_headers(),
        params=params,
        timeout=30,
    )

    if response.status_code == 404:
        return None

    if response.status_code != 200:
        raise RuntimeError(
            "Gagal membaca file di GitHub.\n"
            f"Status : {response.status_code}\n"
            f"Response: {response.text}"
        )

    data = response.json()

    if isinstance(data, list):
        raise RuntimeError(
            f"'{github_path}' adalah folder di GitHub, bukan file."
        )

    return data.get("sha")


def upload_file(
    local_file: str,
    github_path: str,
    commit_message: str,
    branch: str | None = None,
) -> dict:

    validate_configuration()

    branch = branch or DEFAULT_BRANCH

    file_path = Path(local_file)

    if not file_path.exists():
        raise FileNotFoundError(
            f"Local file not found: {file_path}"
        )

    if branch and not branch_exists(branch):
        raise RuntimeError(
            f"Branch '{branch}' tidak ada di {REPO_OWNER}/{REPO_NAME}. "
            "Ingat: nama branch case-sensitive ('Master' != 'master')."
        )

    encoded_content = base64.b64encode(
        file_path.read_bytes()
    ).decode("utf-8")

    last_error = ""

    for attempt in range(1, MAX_ATTEMPTS + 1):

        payload = {
            "message": commit_message,
            "content": encoded_content,
        }

        if branch:
            payload["branch"] = branch

        sha = get_remote_sha(github_path, branch)

        if sha:
            payload["sha"] = sha

        response = requests.put(
            _contents_url(github_path),
            headers=_headers(),
            json=payload,
            timeout=60,
        )

        if response.status_code in (200, 201):
            return response.json()

        last_error = (
            f"Status : {response.status_code}\n"
            f"Response: {response.text}"
        )

        # 409 = branch/sha berubah di tengah jalan (mis. GitHub Action baru
        # saja push). 422 dengan "sha" = sha basi/tidak dikirim. Ambil ulang
        # sha terbaru lalu coba lagi.
        retryable = response.status_code == 409 or (
            response.status_code == 422 and "sha" in response.text
        )

        if not retryable:
            break

        wait = 2 * attempt
        print(
            f"Konflik sha di branch '{branch or 'default'}' "
            f"(percobaan {attempt}/{MAX_ATTEMPTS}), ulangi dalam {wait} detik..."
        )
        time.sleep(wait)

    raise RuntimeError(
        "GitHub API request failed.\n" + last_error
    )


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

    parser.add_argument(
        "--branch",
        action="append",
        dest="branches",
        help=(
            "Branch tujuan (case-sensitive). Boleh diulang untuk "
            "beberapa branch, mis. --branch Master --branch model_history. "
            "Default: env GITHUB_BRANCH atau default branch repo."
        ),
    )

    args = parser.parse_args()

    branches = args.branches or [DEFAULT_BRANCH]

    for branch in branches:
        result = upload_file(
            local_file=args.local_file,
            github_path=args.github_path,
            commit_message=args.message,
            branch=branch,
        )

        print(f"Upload successful -> branch: {branch or '(default)'}")
        print(f"Commit: {result['commit']['html_url']}")
        print(f"Path  : {result['content']['path']}")


if __name__ == "__main__":
    main()
