from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_DIR = PROJECT_ROOT / "registry"

VALID_TOPICS = {"topic-a", "topic-b"}
REQUIRED_FIELDS = {
    "experiment_id",
    "topic",
    "model",
    "objective",
    "dataset",
    "created_at",
    "metrics",
    "status",
    "owner",
    "kaggle",
    "notebook",
    "previous_experiment",
}


def validate_file(file_path: Path) -> list[str]:
    errors: list[str] = []

    try:
        with file_path.open("r", encoding="utf-8") as file:
            data: dict[str, Any] = json.load(file)
    except json.JSONDecodeError as error:
        return [f"Invalid JSON: {error}"]
    except OSError as error:
        return [f"Cannot read file: {error}"]

    missing_fields = REQUIRED_FIELDS - data.keys()

    if missing_fields:
        errors.append(
            "Missing fields: "
            + ", ".join(sorted(missing_fields))
        )

    if "experiment_id" in data:
        experiment_id = data["experiment_id"]

        if not isinstance(experiment_id, str):
            errors.append("experiment_id must be a string.")

        elif not experiment_id.startswith("EXP-"):
            errors.append("experiment_id must start with 'EXP-'.")

    if "topic" in data and data["topic"] not in VALID_TOPICS:
        errors.append(
            f"Invalid topic: {data['topic']}"
        )

    if "status" in data and data["status"] != "SUCCESS":
        errors.append(
            f"Invalid status: {data['status']}"
        )

    if "metrics" in data:
        metrics = data["metrics"]

        if not isinstance(metrics, dict):
            errors.append("metrics must be an object.")
        else:
            for name, value in metrics.items():
                if isinstance(value, bool) or not isinstance(
                    value, (int, float)
                ):
                    errors.append(
                        f"Metric '{name}' must be numeric."
                    )

    return errors


def main() -> int:
    if not REGISTRY_DIR.exists():
        print("Registry directory does not exist.")
        return 0

    json_files = sorted(REGISTRY_DIR.rglob("*.json"))

    if not json_files:
        print("No registry files found.")
        return 0

    total_errors = 0

    for file_path in json_files:
        errors = validate_file(file_path)

        if errors:
            total_errors += len(errors)

            print(f"\nINVALID: {file_path}")

            for error in errors:
                print(f"  - {error}")
        else:
            print(f"VALID:   {file_path}")

    print()
    print(f"Files checked : {len(json_files)}")
    print(f"Errors        : {total_errors}")

    if total_errors > 0:
        return 1

    print("Registry validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
