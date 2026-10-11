from __future__ import annotations

import json
import sys
from pathlib import Path

# Jangan buat scripts/__pycache__/*.pyc (file biner ini dulu ikut ter-commit
# dan selalu bentrok saat merge antar-branch).
sys.dont_write_bytecode = True


ROOT_DIR = Path(__file__).resolve().parent.parent
REGISTRY_DIR = ROOT_DIR / "registry"
README_FILE = ROOT_DIR / "README.md"


def load_experiments() -> list[dict]:
    experiments = []

    for file_path in sorted(REGISTRY_DIR.rglob("*.json")):

        with file_path.open("r", encoding="utf-8") as file:
            record = json.load(file)

        record["_registry_file"] = str(
            file_path.relative_to(ROOT_DIR)
        ).replace("\\", "/")

        experiments.append(record)

    # Urutan stabil (created_at lalu experiment_id) supaya output selalu sama
    # untuk isi registry yang sama, di branch mana pun dijalankan.
    experiments.sort(
        key=lambda item: (
            item.get("created_at", ""),
            item.get("experiment_id", ""),
        ),
        reverse=True,
    )

    return experiments


def format_metric_value(value) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"

    return str(value)


def get_primary_metric(metrics: dict) -> tuple[str, object]:
    preferred = [
        "f1",
        "accuracy",
        "rmse",
        "mae",
        "r2",
    ]

    for metric_name in preferred:
        if metric_name in metrics:
            return metric_name, metrics[metric_name]

    if metrics:
        first_name = next(iter(metrics))
        return first_name, metrics[first_name]

    return "-", "-"


def generate_recent_experiments_section(
    experiments: list[dict],
) -> list[str]:

    lines = [
        "## Recent Experiments",
        "",
    ]

    if not experiments:
        lines.extend(
            [
                "No experiments have been registered yet.",
                "",
            ]
        )
        return lines

    lines.extend(
        [
            "| Experiment ID | Topic | Model | Primary Metric | Value | Status |",
            "|---|---|---|---|---:|---|",
        ]
    )

    for experiment in experiments[:10]:

        metrics = experiment.get("metrics", {})
        metric_name, metric_value = get_primary_metric(metrics)

        lines.append(
            f"| `{experiment.get('experiment_id', '-')}` "
            f"| {experiment.get('topic', '-')} "
            f"| {experiment.get('model', '-')} "
            f"| {metric_name} "
            f"| {format_metric_value(metric_value)} "
            f"| {experiment.get('status', '-')} |"
        )

    lines.append("")

    return lines


def generate_topic_section(
    topic: str,
    experiments: list[dict],
) -> list[str]:

    topic_experiments = [
        experiment
        for experiment in experiments
        if experiment.get("topic") == topic
    ]

    lines = [
        f"## {topic}",
        "",
        f"**Experiments:** {len(topic_experiments)}",
        "",
    ]

    if not topic_experiments:
        lines.extend(
            [
                "No experiments registered for this topic.",
                "",
            ]
        )
        return lines

    owners = {
        experiment.get("owner")
        for experiment in topic_experiments
        if experiment.get("owner")
    }

    if owners:
        lines.append(
            f"**Owner:** {', '.join(sorted(owners))}"
        )
        lines.append("")

    lines.extend(
        [
            "| Experiment ID | Model | Metric | Value | Date |",
            "|---|---|---|---:|---|",
        ]
    )

    for experiment in topic_experiments:

        metrics = experiment.get("metrics", {})
        metric_name, metric_value = get_primary_metric(metrics)

        created_at = experiment.get("created_at", "-")

        lines.append(
            f"| `{experiment.get('experiment_id', '-')}` "
            f"| {experiment.get('model', '-')} "
            f"| {metric_name} "
            f"| {format_metric_value(metric_value)} "
            f"| {created_at} |"
        )

    lines.append("")

    return lines


def generate_selection_section(
    experiments: list[dict],
) -> list[str]:

    lines = [
        "## Model Selection",
        "",
        "> Selection status is recorded separately from experiment execution.",
        "",
    ]

    selection_groups = {
        "CANDIDATE": [],
        "VALIDATED": [],
        "PROMOTED": [],
    }

    for experiment in experiments:

        selection_status = experiment.get(
            "selection_status"
        )

        if selection_status in selection_groups:
            selection_groups[selection_status].append(
                experiment
            )

    for status, items in selection_groups.items():

        lines.append(f"### {status.title()}")
        lines.append("")

        if not items:
            lines.append("None.")
            lines.append("")
            continue

        for experiment in items:
            lines.append(
                f"- `{experiment.get('experiment_id', '-')}` "
                f"— {experiment.get('model', '-')}"
            )

        lines.append("")

    return lines


def generate_repository_structure() -> list[str]:

    return [
        "## Repository Structure",
        "",
        "```text",
        "model-lab/",
        "├── experiments/",
        "│   ├── topic-a/",
        "│   └── topic-b/",
        "├── registry/",
        "│   ├── topic-a/",
        "│   └── topic-b/",
        "├── scripts/",
        "│   ├── extract_registry.py",
        "│   ├── register_experiment.py",
        "│   ├── validate_registry.py",
        "│   ├── generate_readme.py",
        "│   ├── generate_research_log.py",
        "│   ├── run_pipeline.py",
        "│   ├── sync_branches.py",
        "│   └── github_upload.py",
        "├── README.md",
        "└── research_log.md",
        "```",
        "",
    ]


def main() -> None:

    experiments = load_experiments()

    # Sengaja TIDAK memakai jam saat ini (datetime.now()). Timestamp yang
    # berubah setiap kali workflow jalan membuat README.md selalu berbeda di
    # setiap branch sehingga merge Master <-> model_history pasti konflik.
    # Pakai waktu eksperimen terbaru: deterministik untuk registry yang sama.
    generated_at = (
        experiments[0].get("created_at", "-") if experiments else "-"
    )

    topics = sorted(
        {
            experiment.get("topic")
            for experiment in experiments
            if experiment.get("topic")
        }
    )

    lines = [
        "# model-lab",
        "",
        "Automated experiment tracking and modelling registry "
        "for Glowmatch Platform Modelling.",
        "",
        "> **This README is automatically generated. "
        "Do not edit manually.**",
        "",
        "---",
        "",
        "## Project Status",
        "",
        "| Item | Value |",
        "|---|---:|",
        f"| Total experiments | {len(experiments)} |",
    ]

    for topic in topics:

        count = sum(
            1
            for experiment in experiments
            if experiment.get("topic") == topic
        )

        lines.append(
            f"| {topic} | {count} |"
        )

    if experiments:
        latest = experiments[0]

        lines.append(
            f"| Latest experiment | "
            f"`{latest.get('experiment_id', '-')}` |"
        )

    lines.extend(
        [
            f"| Registry updated | {generated_at} |",
            "",
            "---",
            "",
        ]
    )

    lines.extend(
        generate_recent_experiments_section(experiments)
    )

    lines.append("---")
    lines.append("")

    for topic in topics:
        lines.extend(
            generate_topic_section(
                topic,
                experiments,
            )
        )

    lines.append("---")
    lines.append("")

    lines.extend(
        generate_selection_section(experiments)
    )

    lines.append("---")
    lines.append("")

    lines.extend(
        generate_repository_structure()
    )

    README_FILE.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    print(
        f"README generated successfully: {README_FILE}"
    )


if __name__ == "__main__":
    main()
