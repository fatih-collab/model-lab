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


def test_season_region_features_match_notebook():
    from ml.nb_generated import season_nb as snb

    assert len(snb.REGION_COLS) == 53                          # notebook: "53 fitur warna per region"
    img = np.zeros((512, 512, 3), np.uint8)
    lm = np.zeros((512, 512), np.uint8)
    img[100:400, 150:350] = (220, 170, 140); lm[100:400, 150:350] = 1      # skin
    img[40:100, 120:380] = (60, 40, 30); lm[40:100, 120:380] = 13          # hair
    ids = {"skin": [1, 2], "hair": [13], "eye": [4, 5], "lip": [11, 12], "brow": [6, 7]}
    f = snb.region_color_features(img, lm, ids)
    assert f.shape == (53,)
    assert f[snb.COL_IX["skin_L"]] > f[snb.COL_IX["hair_L"]] and f[snb.COL_IX["dL_skin_hair"]] > 0
    assert np.isnan(f[snb.COL_IX["eye_L"]])                    # region tidak ada -> NaN (seperti training)


def test_season_pooling_drop_zero_weight_is_exact():
    from ml.nb_generated import season_nb as snb

    rng = np.random.default_rng(0)
    ps = [rng.dirichlet(np.ones(12), size=3) for _ in range(4)]
    full = snb.pool(ps, (0.1, 0.0, 0.3, 0.6))
    slim = snb.pool([ps[0], ps[2], ps[3]], (0.1, 0.3, 0.6))
    assert np.allclose(full, slim)                             # dasar aman membuang emb_lr_orig saat repack


@needs_nb
def test_manifest_reported_values():
    manifest = json.loads((BACKEND / "models" / "manifest.json").read_text())["modules"]
    ut, ss = manifest["undertone"], manifest["season"]
    assert ut["reported"]["ensemble_weights"] == {"logreg (tuned)": 0.0, "svm (tuned)": 0.171,
                                                  "extratrees (tuned)": 0.0, "convnext_finetune": 0.829}
    assert ss["reported"]["final_method"] == "ensemble"
    assert len(ss["class_names"]) == 12
    assert ss["labels"]["estate_soft"] == {"name": "Soft Summer", "family": "Summer", "subtype": "soft",
                                           "undertone": "cool"}
    fams = {v["family"] for v in ss["labels"].values() if v["undertone"] == "warm"}
    assert fams == {"Spring", "Autumn"}


def test_weights_match_tolerates_rounding():
    assert em._weights_match({"svm (tuned)": 0.17086, "convnext_finetune": 0.82914},
                             {"logreg (tuned)": 0.0, "svm (tuned)": 0.171, "convnext_finetune": 0.829})
    assert not em._weights_match({"svm (tuned)": 0.5, "convnext_finetune": 0.5},
                                 {"svm (tuned)": 0.171, "convnext_finetune": 0.829})
