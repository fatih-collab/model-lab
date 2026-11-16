"""Glue code inferensi diuji dengan model kecil berbobot acak (lihat conftest.py)."""
import os
import sys
import types
from pathlib import Path

import joblib
import numpy as np
import pytest
import torch

from ml.nb_generated import season_nb as snb
from ml.nb_generated import undertone_nb as unb


def wrist_roi(seed=0):
    rng = np.random.default_rng(seed)
    img = np.clip(np.full((300, 400, 3), (215, 160, 120)) + rng.normal(0, 4, (300, 400, 3)), 0, 255).astype(np.uint8)
    img[:, 150:154] = (150, 120, 130)
    return img


# ------------------------------------------------------------------------------------------- undertone
def test_undertone_predict(undertone_model):
    r = undertone_model.predict(wrist_roi())
    assert r.label in ("cool", "neutral", "warm")
    assert abs(sum(r.probs.values()) - 1) < 1e-3
    assert set(r.components) == {"svm (tuned)", "convnext_finetune"}
    assert len(undertone_model.ft_models) == 2


def test_undertone_features_layout(undertone_model):
    from PIL import Image
    x = undertone_model.features(Image.fromarray(wrist_roi()))
    assert x.shape == (1, 384 * 2 + 61)                        # [DINOv2 mean-patch, CLS] + 61 fitur warna


def test_undertone_ensemble_matches_manual_weighting(undertone_model):
    r = undertone_model.predict(wrist_roi(1))
    w = undertone_model.weights
    manual = {c: w["svm (tuned)"] * r.components["svm (tuned)"][c] + w["convnext_finetune"] * r.components["convnext_finetune"][c]
              for c in r.probs}
    assert all(abs(manual[c] - r.probs[c]) < 2e-3 for c in r.probs)


def test_compat_loads_pickle_from_notebook_main(tmp_path):
    """Pickle dari notebook merujuk __main__.SafePCA; load_notebook_joblib harus tetap bisa memuatnya."""
    from ml.compat import load_notebook_joblib

    main = sys.modules["__main__"]
    NbSafePCA = types.new_class("SafePCA", (unb.SafePCA,))
    NbSafePCA.__module__, NbSafePCA.__qualname__ = "__main__", "SafePCA"
    had = hasattr(main, "SafePCA")
    old = getattr(main, "SafePCA", None)
    main.SafePCA = NbSafePCA
    obj = NbSafePCA(n_components=2).fit(np.random.default_rng(0).normal(size=(10, 4)))
    joblib.dump(obj, tmp_path / "nb.joblib")
    del main.SafePCA                                           # proses lain (uvicorn) tidak punya class ini
    try:
        loaded = load_notebook_joblib(tmp_path / "nb.joblib")
        assert loaded.n_components_ == 2
    finally:
        if had:
            main.SafePCA = old
        elif hasattr(main, "SafePCA"):
            del main.SafePCA


# ---------------------------------------------------------------------------------------------- season
def test_season_predict(season_model):
    from tests.tiny_models import fake_face

    r = season_model.predict(fake_face())
    assert r.probs.shape == (12,) and abs(r.probs.sum() - 1) < 1e-6
    assert r.top in r.candidates and r.candidates[0] == r.top
    assert r.status in ("yakin", "perlu_konfirmasi") and 0 <= r.p_warm <= 1
    assert set(r.components) == {"convnext_t", "lgb_flat", "lgb_hier"}
    assert r.mask_source == "pyfacer" and r.rgbm.shape == (96, 96, 3)


def test_season_top_is_hierarchical_decision(season_model):
    """Keputusan = season bermassa terbesar lalu sub terbaik (== hierarchical_decode notebook & rules engine)."""
    from app.rules_engine import family_first
    from tests.tiny_models import MANIFEST, fake_face

    for seed in range(3):
        r = season_model.predict(fake_face(seed=seed))
        assert r.top == r.class_names[int(snb.hierarchical_decode(r.probs[None])[1][0])]
        assert r.top == family_first(dict(zip(r.class_names, r.probs)), MANIFEST["season"]["labels"])


def test_season_matches_manual_combination(season_model):
    from tests.tiny_models import fake_face

    r = season_model.predict(fake_face(seed=1))
    w, c = season_model.b["weights"], {k: np.array(v) for k, v in r.components.items()}
    manual = w["deep"] * c["convnext_t"] + w["lgb"] * (c["lgb_flat"] + c["lgb_hier"]) / 2
    assert np.allclose(manual / manual.sum(), r.probs, atol=2e-3)


def test_rgbm_blackens_background_like_training_cache(season_model):
    from tests.tiny_models import fake_face, fake_label_map

    img = fake_face()
    lm = fake_label_map(*img.shape[:2])
    rgbm = season_model.make_rgbm(img, lm)
    assert rgbm.shape == (96, 96, 3) and rgbm.dtype == np.uint8
    assert rgbm[0, 0].sum() == 0 and rgbm[48, 48].sum() > 0            # sudut = latar hitam, tengah = wajah
    assert (rgbm.max(-1) > 12).mean() > 0.3                             # crop_bbox memangkas latar sebelum letterbox


def test_season_falls_back_to_heuristic_mask_without_face(season_dir):
    from tests.tiny_models import fake_face, load_season

    m = load_season(season_dir, parse_fn=lambda rgb: None)             # pyfacer tidak menemukan wajah
    r = m.predict(fake_face())
    assert r.mask_source == "heuristic" and abs(r.probs.sum() - 1) < 1e-6


def test_lgb_features_follow_training_column_order(season_model):
    from tests.tiny_models import fake_face, fake_label_map

    img = fake_face()
    lm = fake_label_map(*img.shape[:2])
    X, f = season_model.features(img, lm), snb.extract_color_features(img, lm)
    cols = season_model.feature_cols
    assert X.shape == (1, len(cols)) and X.dtype == np.float32
    assert X[0, cols.index("skin_L")] == np.float32(f["skin_L"]) and X[0, cols.index("hair_b")] == np.float32(f["hair_b"])


def test_hiercls_checkpoint_loaded_exactly(season_model, season_dir):
    sd = torch.load(season_dir / "convnext_t_f0.pt", weights_only=True)
    m = season_model.deep_models[0]
    assert not m.training and next(m.parameters()).dtype == torch.float32
    assert torch.equal(m.head_sub.weight, sd["head_sub.weight"])
    assert len(season_model.deep_models) == 2


def test_season_rejects_missing_components(season_bundle):
    from ml.season_model import SeasonModel
    from tests.tiny_models import fake_parse

    with pytest.raises(ValueError):
        SeasonModel(season_bundle, fake_parse, deep_models=[], boosters={"flat": [1], "hier": [[1]]})
    with pytest.raises(ValueError):
        SeasonModel(season_bundle, fake_parse, deep_models=[torch.nn.Identity()], boosters={"flat": [], "hier": []})


@pytest.mark.skipif(not (Path(__file__).resolve().parents[1] / "models" / "pyfacer").exists()
                    or os.environ.get("GLOWMATCH_SLOW_TESTS") != "1",
                    reason="bobot pyfacer asli + GLOWMATCH_SLOW_TESTS=1 (±30 detik di CPU)")
def test_pyfacer_parses_real_face():
    from skimage import data

    from ml.season_model import FaceParser

    parser = FaceParser(Path(__file__).resolve().parents[1] / "models" / "pyfacer")
    lm = parser(data.astronaut())
    assert lm is not None and lm.shape == (512, 512)
    present = set(np.unique(lm).tolist())
    assert {snb.PART_ID[p] for p in ("skin", "hair", "eye", "lip")} <= present
