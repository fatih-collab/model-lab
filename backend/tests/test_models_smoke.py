"""Glue code inferensi diuji dengan model kecil berbobot acak (lihat conftest.py)."""
import sys
import types

import joblib
import numpy as np
import pytest
import torch

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
def face_crop(seed=0):
    rng = np.random.default_rng(seed)
    return np.clip(rng.normal(150, 30, (360, 300, 3)), 0, 255).astype(np.uint8)


def test_season_predict(season_model):
    r = season_model.predict(face_crop())
    assert r.probs.shape == (12,) and abs(r.probs.sum() - 1) < 1e-6
    assert r.top == r.class_names[int(r.probs.argmax())] and r.top in r.candidates
    assert r.status in ("yakin", "perlu_konfirmasi")
    assert 0 <= r.p_warm <= 1
    assert set(r.components) == {"emb_lr", "color_hgb", "ft"}


def test_rgbm_blackens_background(season_model):
    from tests.tiny_models import PARSER_LABELS, fake_label_map

    big, small, valid, _ = season_model.make_rgbm(face_crop())
    lm = fake_label_map(512)
    assert not big[lm == PARSER_LABELS["background"]].any()   # latar hitam seperti RGB-M
    assert big[valid].any() and small.shape == (256, 256, 3)


def test_embedder_keys_and_registers(season_model):
    e = season_model.embedder(np.zeros((1, 256, 256, 3), np.uint8))
    assert list(e) == ["cls_last", "mean_last", "mean_L4", "mean_L8"]
    assert season_model.embedder.n_prefix == 1 + 4             # CLS + 4 register token DINOv3
    assert all(v.shape == (1, 64) for v in e.values())


def test_armonet_fp16_checkpoint_loaded_exactly(season_model, season_dir):
    sd = torch.load(season_dir / "ft_s42_f0.pt", weights_only=True)
    m = season_model.ft_models[0]
    assert next(m.parameters()).dtype == torch.float32
    assert torch.equal(m.head12.weight.half(), sd["head12.weight"])


def test_segformer_parser_shapes(tmp_path):
    from ml.season_model import SegformerParser
    from tests.tiny_models import tiny_segformer

    p = SegformerParser(tiny_segformer())
    out = p(np.zeros((2, 64, 64, 3), np.uint8))
    assert out.shape == (2, 64, 64) and out.dtype == np.uint8 and p.label_ids["hair"] == 13


def test_season_rejects_missing_components(season_bundle):
    from ml.season_model import SeasonModel
    from tests.tiny_models import PARSER_LABELS, fake_parse

    with pytest.raises(ValueError):
        SeasonModel(season_bundle, fake_parse, PARSER_LABELS, embedder=None, ft_models=[])
