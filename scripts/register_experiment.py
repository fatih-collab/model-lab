from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_DIR = PROJECT_ROOT / "registry"

VALID_TOPICS = {"topic-a", "topic-b"}
VALID_STATUSES = {"SUCCESS"}


def generate_experiment_id() -> str:
    now = datetime.now(ZoneInfo("Asia/Jakarta"))
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    random_part = uuid.uuid4().hex[:4]
    return f"EXP-{timestamp}-{random_part}"


def validate_metrics(metrics: dict[str, Any]) -> None:
    """
    Validate that all metric values are numeric and finite.
    """
    if not isinstance(metrics, dict):
        raise ValueError("Metrics must be a JSON object.")

    if not metrics:
        raise ValueError("Metrics cannot be empty.")

    for name, value in metrics.items():
        if not isinstance(name, str):
            raise ValueError("Metric names must be strings.")

        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(
                f"Metric '{name}' must be a number, got {type(value).__name__}."
            )


def validate_experiment(data: dict[str, Any]) -> None:
    """
    Validate the complete experiment record.
    """
    required_fields = {
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

    missing = required_fields - data.keys()

    if missing:
        raise ValueError(
            f"Missing required fields: {', '.join(sorted(missing))}"
        )

    if data["topic"] not in VALID_TOPICS:
        raise ValueError(
            f"Invalid topic '{data['topic']}'. "
            f"Expected one of: {', '.join(sorted(VALID_TOPICS))}"
        )

    if data["status"] not in VALID_STATUSES:
        raise ValueError(
            f"Experiment status must be SUCCESS, got '{data['status']}'."
        )

    if not isinstance(data["model"], str) or not data["model"].strip():
        raise ValueError("Model must be a non-empty string.")

    if not isinstance(data["objective"], str) or not data["objective"].strip():
        raise ValueError("Objective must be a non-empty string.")

    if not isinstance(data["dataset"], str) or not data["dataset"].strip():
        raise ValueError("Dataset must be a non-empty string.")

    if not isinstance(data["owner"], str) or not data["owner"].strip():
        raise ValueError("Owner must be a non-empty string.")

    validate_metrics(data["metrics"])


def build_experiment(args: argparse.Namespace) -> dict[str, Any]:
    """
    Build a complete experiment record from CLI arguments.
    """
    experiment_id = generate_experiment_id()

    metrics = json.loads(args.metrics)

    experiment = {
        "experiment_id": experiment_id,
        "topic": args.topic,
        "model": args.model,
        "objective": args.objective,
        "dataset": args.dataset,
        "created_at": datetime.now(ZoneInfo("Asia/Jakarta")).isoformat(),
        "metrics": metrics,
        "status": "SUCCESS",
        "owner": args.owner,
        "kaggle": {
            "version": None,
            "url": None,
        },
        "notebook": None,
        "previous_experiment": None,
    }

    validate_experiment(experiment)

    return experiment


def save_experiment(experiment: dict[str, Any]) -> Path:
    """
    Save experiment as an immutable JSON registry file.
    """
    topic = experiment["topic"]
    experiment_id = experiment["experiment_id"]

    topic_dir = REGISTRY_DIR / topic
    topic_dir.mkdir(parents=True, exist_ok=True)

    output_file = topic_dir / f"{experiment_id}.json"

    if output_file.exists():
        raise FileExistsError(
            f"Experiment file already exists: {output_file}"
        )

    with output_file.open("w", encoding="utf-8") as file:
        json.dump(
            experiment,
            file,
            indent=2,
            ensure_ascii=False,
        )
        file.write("\n")

    return output_file


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Register a successful modelling experiment."
    )

    parser.add_argument(
        "--topic",
        required=True,
        help="Experiment topic, e.g. topic-a or topic-b.",
    )

    parser.add_argument(
        "--model",
        required=True,
        help="Model name.",
    )

    parser.add_argument(
        "--objective",
        required=True,
        help="Experiment objective.",
    )

    parser.add_argument(
        "--dataset",
        required=True,
        help="Dataset identifier/version.",
    )

    parser.add_argument(
        "--metrics",
        required=True,
        help='Metrics as JSON, e.g. \'{"accuracy":0.94,"f1":0.91}\'',
    )

    parser.add_argument(
        "--owner",
        required=True,
        help="Experiment owner.",
    )

    return parser.parse_args()


def main() -> int:
    try:
        args = parse_arguments()
        experiment = build_experiment(args)
        output_file = save_experiment(experiment)

        print("Experiment registered successfully.")
        print(f"Experiment ID : {experiment['experiment_id']}")
        print(f"Topic         : {experiment['topic']}")
        print(f"Model         : {experiment['model']}")
        print(f"Status        : {experiment['status']}")
        print(f"Registry file : {output_file}")

        return 0

    except json.JSONDecodeError as error:
        print(
            f"ERROR: Invalid metrics JSON: {error}",
            file=sys.stderr,
        )
        return 1

    except (ValueError, FileExistsError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    except Exception as error:
        print(
            f"UNEXPECTED ERROR: {type(error).__name__}: {error}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
