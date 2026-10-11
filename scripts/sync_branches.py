"""
Sinkronkan (merge) satu branch ke branch lain tanpa konflik pada file
yang di-generate otomatis.

Contoh (lokal maupun di GitHub Actions):
    python scripts/sync_branches.py --source model_history --target Master --push
    python scripts/sync_branches.py --source Master --target model_history --push

Cara kerja:
  1. fetch origin, checkout branch target sesuai origin/<target>
  2. git merge origin/<source> --no-commit
  3. konflik pada file hasil generate (README.md, research_log.md,
     scripts/__pycache__/*) diselesaikan otomatis -> file itu akan dibuat
     ulang dari registry gabungan, jadi isinya pasti benar.
  4. bila masih ada konflik di file lain (registry/*.json, notebook, script)
     merge dibatalkan dan daftar file ditampilkan -> harus dicek manual.
  5. jalankan pipeline (extract -> validate -> README -> research log),
     commit, lalu push (opsional) dengan retry.

Nama branch case-sensitive: 'Master' tidak sama dengan 'master'.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# File yang SELALU dibuat ulang oleh pipeline -> aman di-resolve otomatis.
GENERATED_FILES = {"README.md", "research_log.md"}
GENERATED_PREFIXES = ("scripts/__pycache__/",)

COMMIT_PATHS = ["registry", "experiments", "README.md", "research_log.md"]


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} gagal:\n{result.stdout}{result.stderr}"
        )
    return result


def is_generated(path: str) -> bool:
    return path in GENERATED_FILES or path.startswith(GENERATED_PREFIXES)


def ensure_clean_worktree() -> None:
    status = git("status", "--porcelain", "--untracked-files=no").stdout.strip()
    if status:
        raise RuntimeError(
            "Working tree tidak bersih. Commit/stash perubahan dulu:\n" + status
        )


def run_pipeline() -> None:
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "run_pipeline.py")],
        cwd=PROJECT_ROOT,
        env=env,
    )
    if result.returncode != 0:
        raise RuntimeError("Pipeline registry gagal setelah merge.")


def untrack_pycache() -> None:
    git("rm", "-r", "-q", "--cached", "--ignore-unmatch", "scripts/__pycache__")


def merge(source: str, target: str) -> bool:
    """Return True bila ada perubahan yang perlu di-commit."""
    git("fetch", "origin", source, target)
    git("checkout", "-q", "-B", target, f"origin/{target}")

    merge_result = git(
        "merge", "--no-ff", "--no-commit", f"origin/{source}", check=False
    )
    print(merge_result.stdout.strip())

    if "Already up to date" in merge_result.stdout:
        return False

    conflicted = [
        line
        for line in git("diff", "--name-only", "--diff-filter=U").stdout.splitlines()
        if line.strip()
    ]

    real_conflicts = [path for path in conflicted if not is_generated(path)]

    if real_conflicts:
        git("merge", "--abort", check=False)
        raise RuntimeError(
            "Konflik pada file yang BUKAN hasil generate, cek manual:\n  - "
            + "\n  - ".join(real_conflicts)
        )

    for path in conflicted:
        if path.startswith(GENERATED_PREFIXES):
            git("rm", "-q", "--cached", "--ignore-unmatch", path)
            (PROJECT_ROOT / path).unlink(missing_ok=True)
        else:
            # Ambil versi mana saja; isinya akan ditimpa oleh pipeline.
            git("checkout", "--ours", "--", path)
            git("add", path)
        print(f"Auto-resolve file hasil generate: {path}")

    return True


def commit_and_push(source: str, target: str, push: bool) -> None:
    untrack_pycache()
    run_pipeline()

    git("add", "-A", "--", *COMMIT_PATHS)
    # Notebook di root yang sudah dipindah oleh extract_registry.py
    git("add", "-u", "--", ".")
    untrack_pycache()

    has_merge = (PROJECT_ROOT / ".git" / "MERGE_HEAD").exists()
    has_staged = git("diff", "--cached", "--quiet", check=False).returncode != 0

    if not has_merge and not has_staged:
        print("Tidak ada perubahan untuk di-commit.")
        return

    git("commit", "-q", "-m", f"Sync {source} into {target} (auto-resolve generated files)")
    print(git("log", "-1", "--oneline").stdout.strip())

    if not push:
        print(f"Selesai (belum di-push). Jalankan: git push origin {target}")
        return

    for attempt in range(1, 6):
        result = git("push", "origin", f"HEAD:{target}", check=False)
        if result.returncode == 0:
            print(f"Push ke {target} berhasil.")
            return
        print(f"Push ditolak (percobaan {attempt}/5), sinkron ulang...\n{result.stderr}")
        # Branch target berubah di remote -> ulangi seluruh proses dari awal.
        git("merge", "--abort", check=False)
        git("reset", "-q", "--hard")
        if merge(source, target):
            commit_and_push(source, target, push=False)

    raise RuntimeError(f"Gagal push ke {target} setelah 5 percobaan.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--source", required=True, help="Branch sumber, mis. model_history")
    parser.add_argument("--target", required=True, help="Branch tujuan, mis. Master")
    parser.add_argument("--push", action="store_true", help="Push hasil ke origin")
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Lewati cek working tree bersih (dipakai di CI).",
    )
    args = parser.parse_args()

    if args.source == args.target:
        print("ERROR: source dan target tidak boleh sama.", file=sys.stderr)
        return 1

    try:
        if not args.allow_dirty:
            ensure_clean_worktree()

        changed = merge(args.source, args.target)

        if not changed:
            print(f"{args.target} sudah berisi semua commit dari {args.source}.")
            return 0

        commit_and_push(args.source, args.target, args.push)
        return 0

    except RuntimeError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
