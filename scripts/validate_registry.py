from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
REGISTRY_DIR = ROOT_DIR / "registry"

EXPERIMENT_ID_PATTERN = re.compile(
    r"^EXP-\d{8}-\d{6}-[a-zA-Z0-9]{4}$"
)

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
}


def fail(message: str) -> None:
    print(f"[ERROR] {message}")
    sys.exit(1)


def validate_experiment(record: dict, file_path: Path) -> list[str]:
    errors: list[str] = []

    # ---------------------------------------------------------
    # Required fields
    # ---------------------------------------------------------
    missing_fields = REQUIRED_FIELDS - record.keys()

    if missing_fields:
        errors.append(
            f"missing fields: {', '.join(sorted(missing_fields))}"
        )

    # ---------------------------------------------------------
    # Experiment ID
    # ---------------------------------------------------------
    experiment_id = record.get("experiment_id")

    if not isinstance(experiment_id, str):
        errors.append("experiment_id must be a string")

    elif not EXPERIMENT_ID_PATTERN.match(experiment_id):
        errors.append(
            "experiment_id has invalid format "
            "(expected EXP-YYYYMMDD-HHMMSS-XXXX)"
        )

    # ---------------------------------------------------------
    # Topic
    # ---------------------------------------------------------
    topic = record.get("topic")

    if not isinstance(topic, str) or not topic.strip():
        errors.append("topic must be a non-empty string")

    # ---------------------------------------------------------
    # Model
    # ---------------------------------------------------------
    model = record.get("model")

    if not isinstance(model, str) or not model.strip():
        errors.append("model must be a non-empty string")

    # ---------------------------------------------------------
    # Objective
    # ---------------------------------------------------------
    objective = record.get("objective")

    if not isinstance(objective, str) or not objective.strip():
        errors.append("objective must be a non-empty string")

    # ---------------------------------------------------------
    # Dataset
    # ---------------------------------------------------------
    dataset = record.get("dataset")

    if not isinstance(dataset, str) or not dataset.strip():
        errors.append("dataset must be a non-empty string")

    # ---------------------------------------------------------
    # Created at
    # ---------------------------------------------------------
    created_at = record.get("created_at")

    if not isinstance(created_at, str) or not created_at.strip():
        errors.append("created_at must be a non-empty string")

    # ---------------------------------------------------------
    # Metrics
    # ---------------------------------------------------------
    metrics = record.get("metrics")

    if not isinstance(metrics, dict):
        errors.append("metrics must be an object/dictionary")

    else:
        if not metrics:
            errors.append("metrics must not be empty")

        for metric_name, metric_value in metrics.items():

            if not isinstance(metric_name, str):
                errors.append("metric names must be strings")
                continue

            if isinstance(metric_value, bool):
                errors.append(
                    f"metric '{metric_name}' must be numeric"
                )
                continue

            if not isinstance(metric_value, (int, float)):
                errors.append(
                    f"metric '{metric_name}' must be numeric"
                )
                continue

            if not math.isfinite(float(metric_value)):
                errors.append(
                    f"metric '{metric_name}' must be finite"
                )

    # ---------------------------------------------------------
    # Status
    # ---------------------------------------------------------
    status = record.get("status")

    if status != "SUCCESS":
        errors.append(
            f"status must be SUCCESS for registry records, "
            f"got {status!r}"
        )

    # ---------------------------------------------------------
    # Owner
    # ---------------------------------------------------------
    owner = record.get("owner")

    if not isinstance(owner, str) or not owner.strip():
        errors.append("owner must be a non-empty string")

    # ---------------------------------------------------------
    # Topic directory consistency
    # ---------------------------------------------------------
    if isinstance(topic, str):
        parent_topic = file_path.parent.name

        if parent_topic != topic:
            errors.append(
                f"topic mismatch: JSON says '{topic}', "
                f"but file is inside '{parent_topic}'"
            )

    return errors


def main() -> None:
    print("Validating experiment registry...")
    print()

    if not REGISTRY_DIR.exists():
        fail(f"Registry directory not found: {REGISTRY_DIR}")

    json_files = sorted(REGISTRY_DIR.rglob("*.json"))

    if not json_files:
        print("[WARNING] No experiment records found.")
        print("Registry structure is valid, but there are no experiments yet.")
        return

    all_errors: list[str] = []
    experiment_ids: dict[str, Path] = {}

    for file_path in json_files:

        relative_path = file_path.relative_to(ROOT_DIR)

        try:
            with file_path.open("r", encoding="utf-8") as file:
                record = json.load(file)

        except json.JSONDecodeError as exc:
            all_errors.append(
                f"{relative_path}: invalid JSON ({exc})"
            )
            continue

        except OSError as exc:
            all_errors.append(
                f"{relative_path}: cannot read file ({exc})"
            )
            continue

        if not isinstance(record, dict):
            all_errors.append(
                f"{relative_path}: root JSON value must be an object"
            )
            continue

        errors = validate_experiment(record, file_path)

        if errors:
            for error in errors:
                all_errors.append(
                    f"{relative_path}: {error}"
                )

        experiment_id = record.get("experiment_id")

        if isinstance(experiment_id, str):

            if experiment_id in experiment_ids:
                previous_file = experiment_ids[experiment_id]

                all_errors.append(
                    f"duplicate experiment_id '{experiment_id}': "
                    f"{previous_file} and {relative_path}"
                )

            else:
                experiment_ids[experiment_id] = relative_path

    # ---------------------------------------------------------
    # Final result
    # ---------------------------------------------------------
    print(f"Records checked : {len(json_files)}")
    print(f"Unique IDs      : {len(experiment_ids)}")
    print()

    if all_errors:
        print("Registry validation FAILED.")
        print()

        for error in all_errors:
            print(f"- {error}")

        sys.exit(1)

    print("Registry validation PASSED.")
    print("All experiment records are structurally valid.")


if __name__ == "__main__":
    main()
