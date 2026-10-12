# model-lab

Automated experiment tracking and modelling registry for Glowmatch Platform Modelling.

> **This README is automatically generated. Do not edit manually.**

---

## Project Status

| Item | Value |
|---|---:|
| Total experiments | 11 |
| topic-a | 5 |
| topic-b | 6 |
| Latest experiment | `EXP-20261012-191927-3fc3` |
| README generated | 2026-10-12 12:19:27 UTC |

---

## Recent Experiments

| Experiment ID | Topic | Model | Primary Metric | Value | Status |
|---|---|---|---|---:|---|
| `EXP-20261012-191927-3fc3` | topic-a | DINOv3 ViT | f1 | 0.3232 | SUCCESS |
| `EXP-20261008-163613-7e87` | topic-b | Ensemble(svm (tuned), convnext_finetune) on dinov2_vits14 + color | f1 | 68.9834 | SUCCESS |
| `EXP-20261008-145741-57f4` | topic-b | ConvNeXt-Tiny + XGBoost | f1 | 60.6798 | SUCCESS |
| `EXP-20261007-202830-6697` | topic-b | Enhanced Journal CNN | f1 | 50.5019 | SUCCESS |
| `EXP-20261007-200149-7175` | topic-b | ResNet-50 | f1 | 53.4304 | SUCCESS |
| `EXP-20261007-194428-8b7e` | topic-b | ConvNeXt V2 | f1 | 55.7011 | SUCCESS |
| `EXP-20261007-193310-43fb` | topic-b | ConvNeXt V2 | f1 | 55.7011 | SUCCESS |
| `EXP-20261007-141215-f4c5` | topic-a | FaRL16 | f1 | 0.2741 | SUCCESS |
| `EXP-20261007-131650-8bb4` | topic-a | EfficientNet-B0 | f1 | 0.2585 | SUCCESS |
| `EXP-20261007-111955-3fc1` | topic-a | EfficientNet-B0 | f1 | 0.2515 | SUCCESS |

---

## topic-a

**Experiments:** 5

**Owner:** Fatih Itsbatul Haq

| Experiment ID | Model | Metric | Value | Date |
|---|---|---|---:|---|
| `EXP-20261012-191927-3fc3` | DINOv3 ViT | f1 | 0.3232 | 2026-10-12T19:19:27.721356+07:00 |
| `EXP-20261007-141215-f4c5` | FaRL16 | f1 | 0.2741 | 2026-10-07T14:12:15.241081+07:00 |
| `EXP-20261007-131650-8bb4` | EfficientNet-B0 | f1 | 0.2585 | 2026-10-07T13:16:50.192024+07:00 |
| `EXP-20261007-111955-3fc1` | EfficientNet-B0 | f1 | 0.2515 | 2026-10-07T11:19:55.485775+07:00 |
| `EXP-20261006-152728-5f94` | EfficientNet-B0 | f1 | 0.2604 | 2026-10-06T15:27:28.219072+07:00 |

## topic-b

**Experiments:** 6

**Owner:** Egyanta Bareka Sebayang

| Experiment ID | Model | Metric | Value | Date |
|---|---|---|---:|---|
| `EXP-20261008-163613-7e87` | Ensemble(svm (tuned), convnext_finetune) on dinov2_vits14 + color | f1 | 68.9834 | 2026-10-08T16:36:13.387054+07:00 |
| `EXP-20261008-145741-57f4` | ConvNeXt-Tiny + XGBoost | f1 | 60.6798 | 2026-10-08T14:57:41.965446+07:00 |
| `EXP-20261007-202830-6697` | Enhanced Journal CNN | f1 | 50.5019 | 2026-10-07T20:28:30.665876+07:00 |
| `EXP-20261007-200149-7175` | ResNet-50 | f1 | 53.4304 | 2026-10-07T20:01:49.759016+07:00 |
| `EXP-20261007-194428-8b7e` | ConvNeXt V2 | f1 | 55.7011 | 2026-10-07T19:44:28.643913+07:00 |
| `EXP-20261007-193310-43fb` | ConvNeXt V2 | f1 | 55.7011 | 2026-10-07T19:33:10.144459+07:00 |

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
