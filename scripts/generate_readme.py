from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_DIR = PROJECT_ROOT / "registry"
README_FILE = PROJECT_ROOT / "README.md"


def load_experiments() -> list[dict[str, Any]]:
    experiments = []

    if not REGISTRY_DIR.exists():
        return experiments

    for file_path in sorted(REGISTRY_DIR.rglob("*.json")):
        with file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        data["_registry_file"] = file_path.relative_to(
            PROJECT_ROOT
        ).as_posix()

        experiments.append(data)

    experiments.sort(
        key=lambda item: item.get("created_at", ""),
        reverse=True,
    )

    return experiments


def format_metric(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{value:.4f}"

    return str(value)


def generate_dashboard(experiments: list[dict[str, Any]]) -> str:
    successful = [
        experiment
        for experiment in experiments
        if experiment.get("status") == "SUCCESS"
    ]

    topic_a = [
        experiment
        for experiment in successful
        if experiment.get("topic") == "topic-a"
    ]

    topic_b = [
        experiment
        for experiment in successful
        if experiment.get("topic") == "topic-b"
    ]

    lines = [
        "# model-lab",
        "",
        "Automated experiment tracking and modelling registry",
        "for Glowmatch Platform.",
        "",
        "---",
        "",
        "## Project Status",
        "",
        "| Item | Status |",
        "|---|---|",
        "| Repository | Active |",
        "| Experiment tracking | Active |",
        "| Kaggle integration | Planned |",
        "| GitHub automation | Planned |",
        "| Platform integration | Planned |",
        "",
        "---",
        "",
        "## Experiment Statistics",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Total successful experiments | {len(successful)} |",
        f"| Topic A experiments | {len(topic_a)} |",
        f"| Topic B experiments | {len(topic_b)} |",
        "",
        "---",
        "",
        "## Recent Successful Experiments",
        "",
    ]

    if not successful:
        lines.append("No successful experiments yet.")
    else:
        lines.extend(
            [
                "| Experiment ID | Topic | Model | Created At |",
                "|---|---|---|---|",
            ]
        )

        for experiment in successful[:10]:
            lines.append(
                f"| `{experiment['experiment_id']}` "
                f"| {experiment['topic']} "
                f"| {experiment['model']} "
                f"| {experiment['created_at']} |"
            )

    lines.extend(
        [
            "",
            "---",
            "",
            "## Repository Structure",
            "",
            "```text",
            "model-lab/",
            "├── README.md",
            "├── research_log.md",
            "│",
            "├── registry/",
            "│   ├── topic-a/",
            "│   └── topic-b/",
            "│",
            "├── experiments/",
            "│   ├── topic-a/",
            "│   └── topic-b/",
            "│",
            "└── scripts/",
            "    ├── register_experiment.py",
            "    ├── generate_readme.py",
            "    ├── generate_research_log.py",
            "    └── validate_registry.py",
            "```",
            "",
            "---",
            "",
            "## Workflow",
            "",
            "```text",
            "Kaggle",
            "   ↓",
            "Experiment",
            "   ↓",
            "Validation",
            "   ↓",
            "Experiment Registry",
            "   ↓",
            "README + Research Log",
            "   ↓",
            "Candidate",
            "   ↓",
            "Validated",
            "   ↓",
            "Promoted",
            "   ↓",
            "Final Platform",
            "```",
            "",
            "---",
            "",
            "> This README is generated automatically from the experiment registry.",
            "> Do not edit the generated sections manually.",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> int:
    experiments = load_experiments()
    content = generate_dashboard(experiments)

    README_FILE.write_text(
        content,
        encoding="utf-8",
    )

    print(f"README generated: {README_FILE}")
    print(f"Experiments found: {len(experiments)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
