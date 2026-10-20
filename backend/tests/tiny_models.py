"""
Model KECIL berbobot acak dengan antarmuka & format artefak yang sama persis dengan hasil notebook.
Dipakai oleh test (glue code: urutan fitur, kunci checkpoint, dtype, pooling, loader) dan scripts/mock_server.py
(demo frontend sebelum bobot asli tersedia). Angka prediksinya TIDAK bermakna.
"""
import copy
import json
from pathlib import Path
from unittest import mock

import joblib
import numpy as np
import torch
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from ml.nb_generated import season_nb as snb
from ml.nb_generated import undertone_nb as unb

BACKEND = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((BACKEND / "models" / "manifest.json").read_text())["modules"]
# id2label parser jonathandinu/face-parsing (dari output sel 3.3 notebook season)
PARSER_LABELS = {"background": 0, "skin": 1, "nose": 2, "eye_g": 3, "l_eye": 4, "r_eye": 5, "l_brow": 6, "r_brow": 7,
                 "l_ear": 8, "r_ear": 9, "mouth": 10, "u_lip": 11, "l_lip": 12, "hair": 13, "hat": 14, "ear_r": 15,
                 "neck_l": 16, "neck": 17, "cloth": 18}
TINY_DINOV3 = dict(hidden_size=64, num_hidden_layers=9, num_attention_heads=4, intermediate_size=128,
                   num_register_tokens=4, patch_size=16, image_size=224)


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
def fake_label_map(size: int) -> np.ndarray:
    """Tata letak wajah sintetis: rambut di atas, kulit oval, mata, alis, bibir."""
    yy, xx = np.mgrid[:size, :size] / size
    lm = np.zeros((size, size), np.uint8)
    lm[((xx - .5) / .36) ** 2 + ((yy - .45) / .45) ** 2 < 1] = PARSER_LABELS["hair"]
    lm[((xx - .5) / .28) ** 2 + ((yy - .55) / .36) ** 2 < 1] = PARSER_LABELS["skin"]
    for cx, lab in ((.4, "l_eye"), (.6, "r_eye")):
        lm[((xx - cx) / .04) ** 2 + ((yy - .5) / .02) ** 2 < 1] = PARSER_LABELS[lab]
        lm[(abs(xx - cx) < .05) & (abs(yy - .45) < .008)] = PARSER_LABELS["l_brow"]
    lm[((xx - .5) / .07) ** 2 + ((yy - .72) / .025) ** 2 < 1] = PARSER_LABELS["u_lip"]
    return lm


def fake_parse(batch: np.ndarray) -> np.ndarray:
    return np.stack([fake_label_map(b.shape[0]) for b in batch])


def tiny_dinov3():
    from transformers import DINOv3ViTConfig, DINOv3ViTModel
    torch.manual_seed(0)
    return DINOv3ViTModel(DINOv3ViTConfig(**TINY_DINOV3)).eval()


def tiny_segformer():
    from transformers import SegformerConfig, SegformerForSemanticSegmentation
    cfg = SegformerConfig(num_labels=19, id2label={v: k for k, v in PARSER_LABELS.items()},
                          label2id=PARSER_LABELS, depths=[1, 1, 1, 1], hidden_sizes=[8, 16, 32, 64],
                          num_attention_heads=[1, 1, 2, 4], decoder_hidden_size=32)
    return SegformerForSemanticSegmentation(cfg).eval()


def build_season_bundle() -> dict:
    classes = MANIFEST["season"]["class_names"]
    seasons, chars = sorted({c.split("_")[0] for c in classes}), sorted({c.split("_")[1] for c in classes})
    rng = np.random.default_rng(0)
    y = np.arange(96) % 12
    Xe, Xr = rng.normal(size=(96, 4 * 64)), rng.normal(size=(96, 53))
    Xr[rng.random(Xr.shape) < 0.1] = np.nan
    return {
        "class_names": classes, "season_names": seasons, "char_names": chars,
        "season_of": np.array([seasons.index(c.split("_")[0]) for c in classes]),
        "char_of": np.array([chars.index(c.split("_")[1]) for c in classes]),
        "warm_of": np.array([int(c.split("_")[0] in snb.WARM_SEASONS) for c in classes]),
        "method": "ensemble", "comp_names": ["emb_lr", "color_hgb", "ft"],
        "comp_temps": {"emb_lr": 1.063, "color_hgb": 1.322, "ft": 1.118}, "ens_weights": (0.1, 0.3, 0.6),
        "temperature": 0.854, "stacker": None, "conf_high": 0.4139, "conformal_qhat": {0.1: 0.93, 0.2: 0.9},
        "models": {"emb_lr": make_pipeline(StandardScaler(), LogisticRegression(C=1e-3, max_iter=500)).fit(Xe, y),
                   "color_hgb": HistGradientBoostingClassifier(max_iter=20).fit(Xr, y)},
        "emb_keys": ["cls_last", "mean_last", "mean_L4", "mean_L8"], "region_parts": snb.REGION_PARTS,
        "reg_keep": np.arange(53), "parse_size": 512, "cache_size": 256, "emb_img_size": 224, "ft_img_size": 224,
        "extra_mean_layers": [4, 8], "ft_input": "masked", "ft_ckpts": ["ft_s42_f0.pt"], "ft_dropout": 0.2,
        "parser": "jonathandinu/face-parsing", "backbone": "facebook/dinov3-vits16-pretrain-lvd1689m",
    }


def build_season_dir(d: Path, season_bundle: dict) -> Path:
    from ml.season_model import ArmoNet

    d.mkdir(parents=True, exist_ok=True)
    joblib.dump(season_bundle, d / "season_bundle.joblib")
    torch.manual_seed(1)
    net = ArmoNet(copy.deepcopy(tiny_dinov3()), 12, 4, 6, 0.2)
    torch.save({n: (v.half() if v.is_floating_point() else v) for n, v in net.state_dict().items()},  # == notebook
               d / "ft_s42_f0.pt")
    return d


def load_season(d: Path):
    import transformers

    from ml.season_model import SeasonModel

    with mock.patch.object(transformers.AutoModel, "from_pretrained", lambda *a, **k: tiny_dinov3()), \
            mock.patch.object(transformers.SegformerForSemanticSegmentation, "from_pretrained",
                              lambda *a, **k: tiny_segformer()):
        m = SeasonModel.load(d)
    m.parse = fake_parse                                       # parser acak tak menghasilkan wajah -> pakai tata letak sintetis
    return m
