# model-lab

Automated experiment tracking and modelling registry for Glowmatch Platform Modelling.

> **This README is automatically generated. Do not edit manually.**

---

## Project Status

| Item | Value |
|---|---:|
| Total experiments | 6 |
| topic-a | 6 |
| Latest experiment | `EXP-20261005-153754-15ef` |
| README generated | 2026-10-05 08:37:54 UTC |

---

## Recent Experiments

| Experiment ID | Topic | Model | Primary Metric | Value | Status |
|---|---|---|---|---:|---|
| `EXP-20261005-153754-15ef` | topic-a | XGBoost-Tuning | f1 | 0.8730 | SUCCESS |
| `EXP-20261005-153744-5ade` | topic-a | XGBoost-Test-E2E | f1 | 0.9800 | SUCCESS |
| `EXP-20261005-152636-b650` | topic-a | XGBoost-Test-E2E | f1 | 0.9800 | SUCCESS |
| `EXP-20261005-014055-afc1` | topic-a | XGBoost-Test-E2E | f1 | 0.9800 | SUCCESS |
| `EXP-20261005-005858-8adf` | topic-a | XGBoost-Test-E2E | f1 | 0.9800 | SUCCESS |
| `EXP-20261004-141919-111f` | topic-a | XGBoost-Test-E2E | f1 | 0.9800 | SUCCESS |

---

## topic-a

**Experiments:** 6

**Owner:** Fatih Itsbatul Haq

| Experiment ID | Model | Metric | Value | Date |
|---|---|---|---:|---|
| `EXP-20261005-153754-15ef` | XGBoost-Tuning | f1 | 0.8730 | 2026-10-05T15:37:54.184247+07:00 |
| `EXP-20261005-153744-5ade` | XGBoost-Test-E2E | f1 | 0.9800 | 2026-10-05T08:37:44.299071+00:00 |
| `EXP-20261005-152636-b650` | XGBoost-Test-E2E | f1 | 0.9800 | 2026-10-05T08:26:36.170281+00:00 |
| `EXP-20261005-014055-afc1` | XGBoost-Test-E2E | f1 | 0.9800 | 2026-10-04T18:40:55.422369+00:00 |
| `EXP-20261005-005858-8adf` | XGBoost-Test-E2E | f1 | 0.9800 | 2026-10-04T17:58:58.399111+00:00 |
| `EXP-20261004-141919-111f` | XGBoost-Test-E2E | f1 | 0.9800 | 2026-10-04T14:19:19.639323+00:00 |

---

## Model Selection

> Selection status is recorded separately from experiment execution.

### Candidate

None.

### Validated

None.

### Promoted

None.

---

## Repository Structure

```text
model-lab/
├── experiments/
│   ├── topic-a/
│   └── topic-b/
├── registry/
│   ├── topic-a/
│   └── topic-b/
├── scripts/
│   ├── register_experiment.py
│   ├── validate_registry.py
│   ├── generate_readme.py
│   └── generate_research_log.py
├── README.md
└── research_log.md
```
