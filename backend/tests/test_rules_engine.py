import json
from pathlib import Path

import numpy as np
import pytest

from app.rules_engine import WHEEL, decide, wheel_neighbors

LABELS = json.loads((Path(__file__).resolve().parents[1] / "models" / "manifest.json").read_text())["modules"]["season"]["labels"]
WARM = {c for c, v in LABELS.items() if v["undertone"] == "warm"}
COOL = set(LABELS) - WARM


def probs(**peaks) -> dict[str, float]:
    p = {c: 0.01 for c in WHEEL}
    p.update(peaks)
    s = sum(p.values())
    return {c: v / s for c, v in p.items()}


def test_wheel_is_consistent():
    assert sorted(WHEEL) == sorted(LABELS)
    for c in WHEEL:                                           # relasi tetangga simetris
        assert all(c in wheel_neighbors(n) for n in wheel_neighbors(c))
    cross = {frozenset((a, b)) for a in WHEEL for b in wheel_neighbors(a) if LABELS[a]["undertone"] != LABELS[b]["undertone"]}
    names = {frozenset(LABELS[c]["name"] for c in pair) for pair in cross}
    assert names == {frozenset({"Light Spring", "Light Summer"}), frozenset({"Bright Spring", "Bright Winter"}),
                     frozenset({"Deep Winter", "Deep Autumn"}), frozenset({"Soft Autumn", "Soft Summer"})}


@pytest.mark.parametrize("seed", range(20))
@pytest.mark.parametrize("undertone,allowed", [("warm", WARM), ("cool", COOL)])
def test_gate_forces_family(seed, undertone, allowed):
    p = dict(zip(WHEEL, np.random.default_rng(seed).dirichlet(np.ones(12))))
    d = decide(p, LABELS, undertone)
    assert d.gate_applied and d.final.id in allowed
    assert d.final.family in d.allowed_families
    assert abs(sum(o.probability for o in d.ranking) - 1) < 1e-3
    assert all(o.probability == 0 for o in d.ranking if o.id not in allowed)


def test_warm_overrides_cool_model_choice_and_flags_conflict():
    d = decide(probs(estate_soft=0.9, autunno_soft=0.05), LABELS, "warm")
    assert d.model_choice == "estate_soft" and d.final.id == "autunno_soft"
    assert d.overridden and d.conflict                         # model season hampir pasti dingin
    assert d.rule.startswith("WARM")


def test_no_conflict_when_season_agrees():
    d = decide(probs(autunno_warm=0.5, autunno_soft=0.3), LABELS, "warm")
    assert d.final.id == "autunno_warm" and not d.overridden and not d.conflict


def test_neutral_follows_season_lean_and_shows_cross_neighbors():
    d = decide(probs(autunno_soft=0.4, estate_soft=0.3), LABELS, "neutral")
    assert not d.gate_applied and d.undertone == "neutral" and d.undertone_source == "wrist_model"
    assert d.final.id == "autunno_soft" and d.lean == "warm"
    rel = {n.id: n.relation for n in d.neighbors}
    assert rel == {"autunno_warm": "same_family", "estate_soft": "cross_undertone"}   # Soft Autumn <-> Soft Summer
    assert all(n.matches_undertone for n in d.neighbors)


def test_neutral_true_season_adds_opposite_side_option():
    d = decide(probs(primavera_warm=0.5, inverno_cool=0.2), LABELS, "neutral")
    assert d.final.id == "primavera_warm"
    assert [n.relation for n in d.neighbors] == ["same_family", "same_family", "opposite_side_best"]
    assert d.neighbors[-1].id == "inverno_cool"


def test_missing_wrist_behaves_like_neutral():
    d = decide(probs(inverno_deep=0.6), LABELS, None)
    assert not d.gate_applied and d.undertone_source == "season_model" and d.final.id == "inverno_deep"


def test_gated_neighbors_marked_for_manual_swap():
    d = decide(probs(autunno_soft=0.6), LABELS, "warm")
    soft_summer = next(n for n in d.neighbors if n.id == "estate_soft")
    assert soft_summer.relation == "cross_undertone" and not soft_summer.matches_undertone
    assert soft_summer.probability == 0 and soft_summer.model_probability > 0


def test_rejects_incomplete_probs():
    with pytest.raises(ValueError):
        decide({"autunno_soft": 1.0}, LABELS, "warm")
