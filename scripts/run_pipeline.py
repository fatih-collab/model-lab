from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"


def run_script(script_name: str) -> None:
    script_path = SCRIPTS_DIR / script_name

    print(f"\nRunning: {script_name}")
    print("-" * 60)

    # PYTHONDONTWRITEBYTECODE=1 -> tidak ada __pycache__/*.pyc yang ikut ter-commit.
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=PROJECT_ROOT,
        env=env,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"{script_name} failed with exit code "
            f"{result.returncode}"
        )


def main() -> int:
    try:
        run_script("extract_registry.py")
        run_script("validate_registry.py")
        run_script("generate_readme.py")
        run_script("generate_research_log.py")

        print("\nPipeline completed successfully.")
        return 0

    except RuntimeError as error:
        print(f"\nERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
