"""
Inferensi modul 12-Season — model Armocromia v3 (notebook Model/armocromia_season_detection_v3.ipynb).

Yang dilayani (dipilih dari prediksi OOF oleh `scripts/extract_models.py repack`, lihat season_bundle.joblib):
    convnext_t  5 fold, TTA flip         input RGB-M 352 px (wajah + rambut, latar hitam) -> 288 px
    LightGBM    lgb_flat + lgb_hier      input 120 fitur warna per organ (extract_color_features)
    P = w * T-scale(convnext_t) + (1 - w) * mean(T-scale(lgb_flat), T-scale(lgb_hier))

Alur per foto (meniru armo_prep.py + armo_train.py, fungsi diambil apa adanya dari ml.nb_generated.season_nb):
    1. masker organ: pyfacer retinaface/mobilenet + farl/lapa/448 -> label PART_ID (LAPA2ID), seperti 60% masker
       training; wajah tidak terdeteksi -> heuristic_labelmap (fallback yang sama dengan armo_prep.build_masks)
    2. fitur warna dari foto + masker -> booster LightGBM (rata-rata 5 fold)
    3. RGB-M = piksel berlabel > 0; crop_bbox + letterbox(CACHE_SIDE, INTER_AREA) == build_image_caches;
       gpu_aug(train=False) == resize evaluasi; normalisasi mean/std backbone timm; flip TTA; combine_heads
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable
from unittest import mock

import cv2
import numpy as np
import torch
import torch.nn as nn

from ml.nb_generated import season_nb as snb

PYFACER_DETECTOR = "mobilenet0.25_Final.pth"
PYFACER_PARSER = "face_parsing.farl.lapa.main_ema_136500_jit191.pt"
CONFORMAL_ALPHA = 0.20          # himpunan kandidat yang memuat jawaban benar ~80%


class FaceParser:
    """pyfacer: deteksi wajah + face parsing FaRL LaPa -> label map PART_ID (== build_masks di armo_prep.py).
    Bobot dibaca dari models/pyfacer/ (scripts/extract_models.py fetch); tidak pernah mengunduh saat runtime."""

    def __init__(self, weights_dir: Path, device: str = "cpu"):
        missing = [f for f in (PYFACER_DETECTOR, PYFACER_PARSER) if not (weights_dir / f).exists()]
        if missing:
            raise FileNotFoundError(f"Bobot pyfacer tidak ada di {weights_dir}: {missing}. "
                                    "Jalankan: python scripts/extract_models.py fetch")
        os.environ.setdefault("MPLBACKEND", "Agg")           # facer mengimpor matplotlib; server tanpa layar
        import facer

        self.facer, self.device = facer, torch.device(device)
        self.det = facer.face_detector("retinaface/mobilenet", device=self.device,
                                       model_path=str(weights_dir / PYFACER_DETECTOR))
        self.parser = facer.face_parser("farl/lapa/448", device=self.device,
                                        model_path=str(weights_dir / PYFACER_PARSER))

    @torch.inference_mode()
    def __call__(self, rgb: np.ndarray) -> np.ndarray | None:
        img = self.facer.hwc2bchw(torch.from_numpy(np.ascontiguousarray(rgb))).to(self.device)
        faces = self.det(img)
        if len(faces.get("scores", [])) == 0:
            return None
        b = int(torch.argmax(faces["scores"]))                  # wajah dengan skor tertinggi (== armo_prep)
        faces = self.parser(img, {k: v[b:b + 1] for k, v in faces.items()})
        seg = faces["seg"]["logits"].argmax(1)[0].cpu().numpy()
        lut = np.array([snb.LAPA2ID[n] for n in faces["seg"]["label_names"]], np.uint8)
        return lut[seg]


def combine_heads(ls: torch.Tensor, lsub: torch.Tensor) -> torch.Tensor:
    """== combine_heads() armo_train.py: P(sub) = P(sub | head sub) * P(season induk | head season), dinormalisasi.
    Ditulis ulang hanya agar indeks SUB2SEASON mengikuti device tensor (di notebook terikat ke DEV global)."""
    s2s = torch.as_tensor(snb.SUB2SEASON, device=ls.device)
    p = lsub.float().softmax(1) * ls.float().softmax(1)[:, s2s]
    return p / p.sum(1, keepdim=True)


def build_hiercls(backbone: str) -> nn.Module:
    """snb.HierCls persis seperti training, tetapi tanpa mengunduh bobot ImageNet (bobot asli dari checkpoint)."""
    import timm

    create = timm.create_model
    with mock.patch.object(timm, "create_model", lambda *a, **k: create(*a, **{**k, "pretrained": False})):
        return snb.HierCls(backbone)


def load_hiercls(path: Path, backbone: str, device: str = "cpu") -> nn.Module:
    m = build_hiercls(backbone)
    m.load_state_dict(torch.load(path, map_location="cpu", weights_only=True))
    return m.float().to(device).eval()


@dataclass
class SeasonResult:
    class_names: list[str]
    probs: np.ndarray                      # (12,) probabilitas terkalibrasi, urut class_names
    top: str                               # keputusan hierarkis: season terbaik, lalu sub-season terbaik
    confidence: float
    status: str                            # yakin | perlu_konfirmasi (ambang dari OOF, lihat repack)
    candidates: list[str]                  # himpunan konformal ~80%
    p_warm: float                          # massa probabilitas Spring + Autumn
    components: dict[str, list[float]] = field(default_factory=dict)
    rgbm: np.ndarray | None = None         # citra RGB-M yang masuk ke convnext_t (debug)
    mask_source: str = "pyfacer"           # pyfacer | heuristic
    ms: float = 0.0


class SeasonModel:
    def __init__(self, bundle: dict, parse_fn: Callable[[np.ndarray], np.ndarray | None], deep_models: list[nn.Module],
                 boosters: dict[str, list], device: str = "cpu"):
        if not deep_models:
            raise ValueError("Tidak ada checkpoint convnext_t yang dimuat.")
        if not boosters.get("flat") or not boosters.get("hier"):
            raise ValueError("Booster LightGBM (lgb_flat / lgb_hier) tidak lengkap.")
        self.b, self.parse, self.deep_models, self.boosters, self.device = bundle, parse_fn, deep_models, boosters, device
        self.class_names = list(bundle["class_names"])
        self.feature_cols = list(bundle["lgb"]["feature_cols"])
        self.hier_kids = {int(s): list(k) for s, k in bundle["lgb"]["hier_kids"].items()}
        self.warm_mask = np.asarray(bundle["warm_of"]) == 1
        self.img_size, self.cache_side = int(bundle["deep"]["img_size"]), int(bundle["cache_side"])
        cfg = getattr(deep_models[0].backbone, "pretrained_cfg", None) or {}     # == main() armo_train.py
        self._mean = torch.tensor(cfg.get("mean", (0.485, 0.456, 0.406)), dtype=torch.float32, device=device).view(1, 3, 1, 1)
        self._std = torch.tensor(cfg.get("std", (0.229, 0.224, 0.225)), dtype=torch.float32, device=device).view(1, 3, 1, 1)

    @classmethod
    def load(cls, model_dir: Path, device: str = "cpu", max_folds: int = 0, parse_fn=None,
             pyfacer_dir: Path | None = None) -> "SeasonModel":
        """max_folds > 0 membatasi jumlah fold convnext_t (lebih cepat, sedikit kurang akurat); LightGBM tetap 5 fold."""
        import joblib
        import lightgbm as lgb

        bundle = joblib.load(model_dir / "season_bundle.joblib")
        if parse_fn is None:
            parse_fn = FaceParser(pyfacer_dir or model_dir.parent / "pyfacer", device)
        ckpts = bundle["deep"]["ckpts"][:max_folds] if max_folds else bundle["deep"]["ckpts"]
        deep = [load_hiercls(model_dir / name, bundle["deep"]["backbone"], device) for name in ckpts]
        booster = lambda f: lgb.Booster(model_file=str(model_dir / f))
        boosters = {"flat": [booster(f) for f in bundle["lgb"]["flat"]],
                    "hier": [[booster(f) for f in fold] for fold in bundle["lgb"]["hier"]]}
        return cls(bundle, parse_fn, deep, boosters, device)

    # ------------------------------------------------------------------------------------------------
    def label_map(self, rgb: np.ndarray) -> tuple[np.ndarray, str]:
        lm = self.parse(rgb)
        if lm is None or not (lm > 0).any():
            return snb.heuristic_labelmap(rgb), "heuristic"
        if lm.shape != rgb.shape[:2]:                           # == load_rgb_lm()
            lm = cv2.resize(lm, (rgb.shape[1], rgb.shape[0]), interpolation=cv2.INTER_NEAREST)
        return lm, "pyfacer"

    def make_rgbm(self, rgb: np.ndarray, lm: np.ndarray) -> np.ndarray:
        """RGB-M (wajah + rambut, latar hitam) lalu crop_bbox + letterbox persis seperti cache 'rgbm' training."""
        a = rgb * (lm > 0)[..., None].astype(np.uint8)
        y0, y1, x0, x1 = snb.crop_bbox(a.max(-1) > 12, *a.shape[:2])
        return snb.letterbox(a[y0:y1, x0:x1], self.cache_side, cv2.INTER_AREA)

    def features(self, rgb: np.ndarray, lm: np.ndarray) -> np.ndarray:
        """Vektor fitur warna dengan urutan kolom training (dicocokkan per nama; region hilang -> NaN)."""
        f = snb.extract_color_features(rgb, lm)
        return np.array([[f.get(c, np.nan) for c in self.feature_cols]], dtype=np.float32)

    def _lgb(self, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        flat = np.mean([b.predict(X) for b in self.boosters["flat"]], axis=0)
        hier = []
        for season_booster, *experts in self.boosters["hier"]:   # P(sub) = P(season) * P(sub | season)
            ps, pt = season_booster.predict(X), np.zeros((len(X), len(self.class_names)))
            for s, expert in enumerate(experts):
                pt[:, self.hier_kids[s]] = ps[:, [s]] * expert.predict(X)
            hier.append(pt)
        return flat, np.mean(hier, axis=0)

    @torch.no_grad()
    def _deep(self, rgbm: np.ndarray) -> np.ndarray:
        x, _ = snb.gpu_aug(torch.from_numpy(rgbm[None]).to(self.device), None, self.img_size, train=False)
        x = (x - self._mean) / self._std
        ps = []
        for m in self.deep_models:                              # == predict(..., tta=True), lalu rata-rata fold
            o1, o2 = m(x), m(torch.flip(x, dims=[-1]))
            ps.append(0.5 * (combine_heads(o1[0], o1[1]) + combine_heads(o2[0], o2[1])))
        return torch.stack(ps).mean(0).float().cpu().numpy().astype(np.float64)

    def predict(self, face_rgb: np.ndarray) -> SeasonResult:
        t0 = time.perf_counter()
        rgb = np.ascontiguousarray(face_rgb)
        lm, source = self.label_map(rgb)
        flat, hier = self._lgb(self.features(rgb, lm))
        rgbm = self.make_rgbm(rgb, lm)
        deep = self._deep(rgbm)

        T, w, tag = self.b["temps"], self.b["weights"], self.b["deep"]["tag"]
        comp = {tag: snb.temp_scale(deep, T[tag]), "lgb_flat": snb.temp_scale(flat, T["lgb_flat"]),
                "lgb_hier": snb.temp_scale(hier, T["lgb_hier"])}
        p = w["deep"] * comp[tag] + w["lgb"] * (comp["lgb_flat"] + comp["lgb_hier"]) / 2
        p = (p / p.sum(1, keepdims=True))[0]

        top = int(snb.hierarchical_decode(p[None])[1][0])
        qhat = self.b["conformal_qhat"].get(CONFORMAL_ALPHA, self.b["conformal_qhat"][min(self.b["conformal_qhat"])])
        in_set = p >= 1.0 - qhat
        in_set[top] = True                                      # keputusan teratas selalu masuk
        order = [top] + [int(i) for i in np.argsort(-p) if int(i) != top]
        return SeasonResult(
            class_names=self.class_names, probs=p, top=self.class_names[top], confidence=float(p[top]),
            status="yakin" if p[top] >= self.b["conf_high"] else "perlu_konfirmasi",
            candidates=[self.class_names[i] for i in order if in_set[i]],
            p_warm=float(p[self.warm_mask].sum()),
            components={k: np.round(v[0], 4).tolist() for k, v in comp.items()},
            rgbm=rgbm, mask_source=source, ms=(time.perf_counter() - t0) * 1000)
