"""
Model KECIL berbobot acak dengan antarmuka & format artefak yang sama persis dengan hasil notebook.
Dipakai oleh test (glue code: urutan fitur, kunci checkpoint, dtype, pooling, loader) dan scripts/mock_server.py
(demo frontend sebelum bobot asli tersedia). Angka prediksinya TIDAK bermakna.
"""
import json
from pathlib import Path
from unittest import mock

import joblib
import numpy as np
import torch
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from ml.nb_generated import season_nb as snb
from ml.nb_generated import undertone_nb as unb

BACKEND = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((BACKEND / "models" / "manifest.json").read_text())["modules"]
TINY_BACKBONE = "convnext_atto"      # arsitektur ConvNeXt kecil timm: format checkpoint HierCls sama dengan convnext_t
TINY_FOLDS = 2


# ------------------------------------------------------------------------------------------- undertone
def tiny_dinov2():
    import timm
    return timm.create_model("vit_small_patch14_dinov2", pretrained=False, num_classes=0, img_size=224, depth=2)


def build_undertone_dir(d: Path) -> Path:
    from ml.undertone_model import build_convnext

    d.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(0)
    X, y = rng.normal(size=(60, 768 + 61)), np.arange(60) % 3
    svm = Pipeline([("sc", StandardScaler()), ("pca", unb.SafePCA(n_components=16, random_state=0)),
                    ("clf", SVC(probability=True, random_state=0))]).fit(X, y)
    bundle = {"class_names": ["cool", "neutral", "warm"], "best_cnn": ["dinov2_vits14"], "use_color": True,
              "weights": {"svm (tuned)": 0.171, "convnext_finetune": 0.829}, "models": {"svm (tuned)": svm},
              "img_size": 224, "n_tta": 8, "use_roi": True, "color_names": [],
              "ft_ckpts": ["convnext_ft_fold0.pth", "convnext_ft_fold1.pth"]}
    joblib.dump(bundle, d / "undertone_bundle.joblib")
    torch.manual_seed(0)
    for name in bundle["ft_ckpts"]:
        torch.save(build_convnext(3).state_dict(), d / name)
    return d


def load_undertone(d: Path):
    import timm

    from ml.undertone_model import UndertoneModel

    tiny = tiny_dinov2()
    with mock.patch.object(timm, "create_model", lambda *a, **k: tiny):          # hindari unduh bobot pretrained
        return UndertoneModel.load(d)


# ---------------------------------------------------------------------------------------------- season
def fake_label_map(h: int, w: int | None = None) -> np.ndarray:
    """Tata letak wajah sintetis berlabel PART_ID: rambut di atas, kulit oval, mata, alis, bibir, latar 0."""
    w = h if w is None else w
    yy, xx = np.mgrid[:h, :w]
    yy, xx = yy / h, xx / w
    P = snb.PART_ID
    lm = np.zeros((h, w), np.uint8)
    lm[((xx - .5) / .36) ** 2 + ((yy - .45) / .45) ** 2 < 1] = P["hair"]
    lm[((xx - .5) / .28) ** 2 + ((yy - .55) / .36) ** 2 < 1] = P["skin"]
    for cx in (.4, .6):
        lm[((xx - cx) / .04) ** 2 + ((yy - .5) / .02) ** 2 < 1] = P["eye"]
        lm[(abs(xx - cx) < .05) & (abs(yy - .45) < .008)] = P["brow"]
    lm[((xx - .5) / .07) ** 2 + ((yy - .72) / .025) ** 2 < 1] = P["lip"]
    return lm


def fake_parse(rgb: np.ndarray) -> np.ndarray:
    """Pengganti pyfacer (bobot 650 MB): selalu 'menemukan' wajah sintetis seukuran gambar."""
    return fake_label_map(*rgb.shape[:2])


def fake_face(h: int = 360, w: int = 300, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    img = np.clip(rng.normal(150, 30, (h, w, 3)), 0, 255).astype(np.uint8)
    lm = fake_label_map(h, w)
    for part, rgb in (("skin", (215, 165, 135)), ("hair", (60, 40, 30)), ("lip", (190, 90, 90))):
        img[lm == snb.PART_ID[part]] = rgb
    return img


def feature_cols() -> list[str]:
    """Urutan kolom fitur seperti color_features.parquet: urutan kunci extract_color_features pada wajah lengkap."""
    img = fake_face()
    return list(snb.extract_color_features(img, fake_label_map(*img.shape[:2])))


def build_season_bundle() -> dict:
    classes = MANIFEST["season"]["class_names"]
    kids = {s: np.where(snb.SUB2SEASON == s)[0].tolist() for s in range(snb.NUM_SEASONS)}
    return {
        "class_names": classes, "labels": MANIFEST["season"]["labels"],
        "warm_of": np.array([int(MANIFEST["season"]["labels"][c]["undertone"] == "warm") for c in classes]),
        "deep": {"tag": "convnext_t", "kind": "cls", "backbone": TINY_BACKBONE, "img_size": 64,
                 "ckpts": [f"convnext_t_f{k}.pt" for k in range(TINY_FOLDS)]},
        "lgb": {"flat": [f"lgb_flat_f{k}.txt" for k in range(TINY_FOLDS)],
                "hier": [[f"lgb_hier_season_f{k}.txt"] + [f"lgb_hier_expert{s}_f{k}.txt" for s in kids]
                         for k in range(TINY_FOLDS)],
                "feature_cols": feature_cols(), "hier_kids": kids},
        "cache_side": 96, "temps": {"convnext_t": 3.0, "lgb_flat": 1.08, "lgb_hier": 1.07},
        "weights": {"deep": 0.9, "lgb": 0.1}, "conf_high": 0.5, "conformal_qhat": {0.1: 0.97, 0.2: 0.94},
    }


def _tiny_booster(n_features: int, n_class: int, seed: int, path: Path) -> None:
    import lightgbm as lgb

    rng = np.random.default_rng(seed)
    y = np.arange(30 * n_class) % n_class
    X = rng.normal(size=(len(y), n_features)) + y[:, None] * 0.1
    params = dict(objective="multiclass", num_class=n_class, num_leaves=4, min_data_in_leaf=2, verbose=-1, seed=seed)
    lgb.train(params, lgb.Dataset(X, y), 3).save_model(str(path))


def build_season_dir(d: Path, season_bundle: dict) -> Path:
    from ml.season_model import build_hiercls

    d.mkdir(parents=True, exist_ok=True)
    joblib.dump(season_bundle, d / "season_bundle.joblib")
    torch.manual_seed(1)
    for name in season_bundle["deep"]["ckpts"]:
        torch.save(build_hiercls(TINY_BACKBONE).state_dict(), d / name)        # == torch.save di armo_train.py
    n_feat, kids = len(season_bundle["lgb"]["feature_cols"]), season_bundle["lgb"]["hier_kids"]
    for k, name in enumerate(season_bundle["lgb"]["flat"]):
        _tiny_booster(n_feat, snb.NUM_CLASSES, k, d / name)
    for k, (season_file, *experts) in enumerate(season_bundle["lgb"]["hier"]):
        _tiny_booster(n_feat, snb.NUM_SEASONS, 10 + k, d / season_file)
        for s, name in enumerate(experts):
            _tiny_booster(n_feat, len(kids[s]), 20 + 10 * k + s, d / name)
    return d


def load_season(d: Path, parse_fn=fake_parse):
    from ml.season_model import SeasonModel

    return SeasonModel.load(d, parse_fn=parse_fn)
