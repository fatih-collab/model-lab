# model-lab

Automated experiment tracking and modelling registry for Glowmatch Platform Modelling.

> **This README is automatically generated. Do not edit manually.**

---

## Project Status

| Item | Value |
|---|---:|
| Total experiments | 3 |
| topic-a | 3 |
| Latest experiment | `EXP-20261005-153812-7506` |
| README generated | 2026-10-06 02:06:19 UTC |

---

## Recent Experiments

| Experiment ID | Topic | Model | Primary Metric | Value | Status |
|---|---|---|---|---:|---|
| `EXP-20261005-153812-7506` | topic-a | XGBoost-Tuning | f1 | 0.8730 | SUCCESS |
| `EXP-20261005-153754-15ef` | topic-a | XGBoost-Tuning | f1 | 0.8730 | SUCCESS |
| `EXP-20261005-153744-5ade` | topic-a | XGBoost-Test-E2E | f1 | 0.9800 | SUCCESS |

---

## topic-a

**Experiments:** 3

**Owner:** Fatih Itsbatul Haq

| Experiment ID | Model | Metric | Value | Date |
|---|---|---|---:|---|
| `EXP-20261005-153812-7506` | XGBoost-Tuning | f1 | 0.8730 | 2026-10-05T15:38:12.808784+07:00 |
| `EXP-20261005-153754-15ef` | XGBoost-Tuning | f1 | 0.8730 | 2026-10-05T15:37:54.184247+07:00 |
| `EXP-20261005-153744-5ade` | XGBoost-Test-E2E | f1 | 0.9800 | 2026-10-05T08:37:44.299071+00:00 |

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
