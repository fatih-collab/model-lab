"""Kode hasil ekstraksi harus identik perilakunya dengan notebook (jumlah fitur, nama kelas, bobot)."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

BACKEND = Path(__file__).resolve().parents[1]
NB_DIR = BACKEND.parent / "Model"
sys.path.insert(0, str(BACKEND / "scripts"))
import extract_models as em  # noqa: E402

needs_nb = pytest.mark.skipif(not NB_DIR.exists(), reason="folder Model/ (notebook) tidak ada")


@needs_nb
def test_generated_code_is_up_to_date(tmp_path):
    em.main(["code", "--out-dir", str(tmp_path)])
    for spec in em.SPECS.values():
        fresh = (tmp_path / f"{spec['module']}.py").read_text()
        committed = (BACKEND / "ml" / "nb_generated" / f"{spec['module']}.py").read_text()
        assert fresh == committed, f"{spec['module']}.py basi — jalankan: python scripts/extract_models.py code"


def test_undertone_color_features_match_notebook():
    from ml.nb_generated import undertone_nb as unb

    rng = np.random.default_rng(0)
    img = np.full((300, 400, 3), (215, 160, 120), np.uint8)
    img = np.clip(img + rng.normal(0, 4, img.shape), 0, 255).astype(np.uint8)
    img[:, 150:154] = (150, 120, 120)
    feats, names = unb.color_features(Image.fromarray(img))
    assert feats.shape == (61,) and len(names) == 61           # notebook: "61 fitur warna"
    assert np.isfinite(feats).all()
    assert unb.CLASS_NAMES == ["cool", "neutral", "warm"]


def test_season_color_features_match_notebook():
    """extract_color_features notebook v3: 20 statistik per organ, kontras kulit-organ, region hilang -> tanpa kunci."""
    from ml.nb_generated import season_nb as snb

    P = snb.PART_ID
    img = np.zeros((300, 300, 3), np.uint8)
    lm = np.zeros((300, 300), np.uint8)
    img[100:280, 80:220] = (220, 170, 140); lm[100:280, 80:220] = P["skin"]
    img[20:100, 60:240] = (60, 40, 30); lm[20:100, 60:240] = P["hair"]
    f = snb.extract_color_features(img, lm)
    assert len([k for k in f if k.startswith("skin_")]) == 20 and f["skin_L"] > f["hair_L"]
    assert f["dL_skin_hair"] > 0 and "eye_L" not in f and np.isnan(f["dL_skin_eye"])
    assert snb.SUB_NAMES[0] == "autunno-deep" and snb.NUM_CLASSES == 12 and snb.CACHE_SIDE == 352


def test_season_hierarchical_decode_is_family_first():
    from app.rules_engine import family_first
    from ml.nb_generated import season_nb as snb

    labels = json.loads((BACKEND / "models" / "manifest.json").read_text())["modules"]["season"]["labels"]
    ids = em.season_ids(snb.SUB_NAMES)
    p = np.full(12, 0.02); p[ids.index("estate_soft")] = 0.30                # sub tertinggi di Summer (massa 0,34)...
    for c, v in (("autunno_deep", 0.14), ("autunno_soft", 0.13), ("autunno_warm", 0.12)):   # ...Autumn 0,39
        p[ids.index(c)] = v
    p /= p.sum()
    sub = snb.hierarchical_decode(p[None])[1][0]
    assert ids[sub] == family_first(dict(zip(ids, p)), labels) == "autunno_deep" != ids[p.argmax()]


def test_build_season_bundle_selects_weight_on_oof_only():
    """repack: bobot dipilih dari OOF, test hanya dilaporkan; ambang & qhat valid; nama file booster tanpa folder."""
    import pandas as pd
    from ml.nb_generated import season_nb as snb

    rng = np.random.default_rng(0)
    n_tr, n_te = 240, 60
    y_tr, y_te = np.arange(n_tr) % 12, np.arange(n_te) % 12
    good = lambda y: np.eye(12)[y] * 3 + rng.random((len(y), 12))               # informatif
    noise = lambda y: rng.random((len(y), 12))                                   # tidak informatif
    norm = lambda p: p / p.sum(1, keepdims=True)
    raw = {"class_names": snb.SUB_NAMES, "models": ["convnext_t", "lgb_flat", "lgb_hier"],
           "temps": {"convnext_t": 1.0, "lgb_flat": 1.0, "lgb_hier": 1.0}, "y_te": y_te,
           "pred_oof": {"convnext_t": norm(good(y_tr)), "lgb_flat": norm(noise(y_tr)), "lgb_hier": norm(noise(y_tr))},
           "pred_test": {"convnext_t": norm(good(y_te)), "lgb_flat": norm(noise(y_te)), "lgb_hier": norm(noise(y_te))},
           "model_zoo": {"convnext_t": {"kind": "cls", "backbone": "convnext_tiny.fb_in22k_ft_in1k", "img_size": 288}},
           "deep_ckpts": {"convnext_t": [f"/kaggle/working/output_v3/weights/convnext_t_f{k}.pt" for k in range(5)]},
           "lgb_models": {"lgb_flat": [[f"weights/lgb_flat_f{k}.txt"] for k in range(5)],
                          "lgb_hier": [[f"weights/lgb_hier_season_f{k}.txt"] + [f"weights/lgb_hier_expert{s}_f{k}.txt"
                                                                              for s in range(4)] for k in range(5)]},
           "lgb_feature_cols": ["skin_L", "hair_L"], "lgb_hier_kids": {s: [3 * s, 3 * s + 1, 3 * s + 2] for s in range(4)},
           "official_test_metrics": {"season_acc": 0.59}, "final_name": "x"}
    meta = pd.DataFrame({"partition": ["train"] * n_tr + ["test"] * n_te, "y_sub": np.r_[y_tr, y_te],
                         "celeba": [True] * (n_tr + n_te)})
    manifest = json.loads((BACKEND / "models" / "manifest.json").read_text())["modules"]["season"]
    b = em.build_season_bundle(raw, meta, manifest)
    assert b["weights"]["deep"] >= 0.9 and abs(b["weights"]["deep"] + b["weights"]["lgb"] - 1) < 1e-6
    assert b["lgb"]["flat"][0] == "lgb_flat_f0.txt" and b["lgb"]["hier"][0][1] == "lgb_hier_expert0_f0.txt"
    assert b["deep"]["ckpts"] == [f"convnext_t_f{k}.pt" for k in range(5)]
    assert 0 < b["conf_high"] <= 1.01 and set(b["conformal_qhat"]) == {0.1, 0.2}
    assert b["metrics"]["oof"]["served"]["sub_acc"] > 0.9 and b["class_names"] == manifest["class_names"]
    meta.loc[n_tr, "y_sub"] = (y_te[0] + 1) % 12                                  # meta dari run lain
    with pytest.raises(ValueError):
        em.build_season_bundle(raw, meta, manifest)


@needs_nb
def test_manifest_reported_values():
    manifest = json.loads((BACKEND / "models" / "manifest.json").read_text())["modules"]
    ut, ss = manifest["undertone"], manifest["season"]
    assert ut["reported"]["ensemble_weights"] == {"logreg (tuned)": 0.0, "svm (tuned)": 0.171,
                                                  "extratrees (tuned)": 0.0, "convnext_finetune": 0.829}
    assert ss["notebook"] == em.SPECS["season"]["notebook"] and ss["serving"]["deep"] == "convnext_t"
    assert ss["class_names"] == em.season_ids(ss["config"]["SUB_NAMES"]) and len(ss["class_names"]) == 12
    assert ss["labels"]["estate_soft"] == {"name": "Soft Summer", "family": "Summer", "subtype": "soft",
                                           "undertone": "cool"}
    fams = {v["family"] for v in ss["labels"].values() if v["undertone"] == "warm"}
    assert fams == {"Spring", "Autumn"}


def test_weights_match_tolerates_rounding():
    assert em._weights_match({"svm (tuned)": 0.17086, "convnext_finetune": 0.82914},
                             {"logreg (tuned)": 0.0, "svm (tuned)": 0.171, "convnext_finetune": 0.829})
    assert not em._weights_match({"svm (tuned)": 0.5, "convnext_finetune": 0.5},
                                 {"svm (tuned)": 0.171, "convnext_finetune": 0.829})
