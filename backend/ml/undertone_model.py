"""
Inferensi modul Undertone — port dari notebook EXP-20261008-163613-7e87:
    sel 8  `Extractor` (DINOv2 frozen: mean patch token + CLS, TTA 8 view)
    sel 13 `make_ft_model` (ConvNeXt-Tiny fine-tune, head Dropout+Linear)
    sel 17 `_feat_single` + `predict_image` (ensemble berbobot)
Fungsi pre-processing/fitur warna diambil langsung dari ml.nb_generated.undertone_nb.
Masukan: ROI pergelangan RGB hasil ml.preprocess.Preprocessor.process_wrist().
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from torchvision import transforms

from ml.compat import load_notebook_joblib
from ml.nb_generated import undertone_nb as unb

DINOV2_TIMM_ID = "vit_small_patch14_dinov2.lvd142m"
FT_KEY = "convnext_finetune"


def build_convnext(n_classes: int) -> nn.Module:
    """Arsitektur make_ft_model() tanpa unduh bobot ImageNet (semua bobot ada di checkpoint fold)."""
    from torchvision.models import convnext_tiny

    m = convnext_tiny(weights=None)
    m.classifier[2] = nn.Sequential(nn.Dropout(0.3), nn.Linear(m.classifier[2].in_features, n_classes))
    return m


def load_convnext_fold(path: Path, n_classes: int, device: str = "cpu") -> nn.Module:
    m = build_convnext(n_classes)
    m.load_state_dict(torch.load(path, map_location="cpu", weights_only=True))
    return m.eval().to(device)


class Dinov2Extractor:
    """== Extractor(kind='vit'): (mean patch token ≈ GAP, CLS token)."""

    def __init__(self, model: nn.Module):
        self.model = model.eval()

    @torch.no_grad()
    def __call__(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        t = self.model.forward_features(x).float()
        npt = getattr(self.model, "num_prefix_tokens", 1)
        return t[:, npt:].mean(1), t[:, 0]


@dataclass
class UndertoneResult:
    label: str
    probs: dict[str, float]
    confidence: float
    components: dict[str, dict[str, float]] = field(default_factory=dict)
    ms: float = 0.0


class UndertoneModel:
    def __init__(self, bundle: dict, extractors: dict, ft_models: list[nn.Module], device: str = "cpu"):
        self.bundle, self.extractors, self.ft_models, self.device = bundle, extractors, ft_models, device
        self.class_names = list(bundle["class_names"])
        self.weights = {k: float(w) for k, w in bundle["weights"].items() if w >= 1e-3}
        self.sk_names = [k for k in self.weights if k != FT_KEY]
        missing = [k for k in self.sk_names if k not in bundle["models"]]
        if missing:
            raise ValueError(f"Model sklearn tidak ada di bundle: {missing}")
        if FT_KEY in self.weights and not ft_models:
            raise ValueError("Bobot convnext_finetune > 0 tetapi tidak ada checkpoint fold yang dimuat.")
        self._to_tensor = transforms.Compose([transforms.ToTensor(), transforms.Normalize(unb.MEAN, unb.STD)])

    @classmethod
    def load(cls, model_dir: Path, device: str = "cpu", max_folds: int = 0) -> "UndertoneModel":
        import timm

        slim, raw = model_dir / "undertone_bundle.joblib", model_dir / "undertone_ensemble.joblib"
        bundle = load_notebook_joblib(slim if slim.exists() else raw)
        extractors = {}
        for name in bundle["best_cnn"]:
            if name != "dinov2_vits14":
                raise NotImplementedError(f"Backbone {name} belum didukung (run terbaik notebook memakai dinov2_vits14).")
            m = timm.create_model(DINOV2_TIMM_ID, pretrained=True, num_classes=0, img_size=bundle["img_size"])
            extractors[name] = Dinov2Extractor(m.to(device))
        ft = []
        if bundle["weights"].get(FT_KEY, 0) >= 1e-3:
            ckpts = bundle.get("ft_ckpts") or sorted(p.name for p in model_dir.glob("convnext_ft_fold*.pth"))
            ckpts = ckpts[:max_folds] if max_folds else ckpts
            ft = [load_convnext_fold(model_dir / c, len(bundle["class_names"]), device) for c in ckpts]
        return cls(bundle, extractors, ft, device)

    def _views(self, roi: Image.Image, n: int | None = None) -> torch.Tensor:
        return torch.stack([self._to_tensor(v) for v in unb.tta_views(roi, n)]).to(self.device)

    @torch.no_grad()
    def features(self, roi: Image.Image) -> np.ndarray:
        """== _feat_single(): [DINOv2 mean-patch, CLS] (rata-rata TTA) + 61 fitur warna."""
        parts = []
        if self.bundle["best_cnn"]:
            x = self._views(roi)
            for name in self.bundle["best_cnn"]:
                a, b = self.extractors[name](x)
                parts.append(np.hstack([a.mean(0).cpu().numpy(), b.mean(0).cpu().numpy()]))
        if self.bundle["use_color"]:
            parts.append(unb.color_features(roi)[0])
        return np.hstack(parts)[None].astype(np.float32)

    @torch.no_grad()
    def predict(self, roi_rgb: np.ndarray) -> UndertoneResult:
        t0 = time.perf_counter()
        roi = Image.fromarray(roi_rgb)
        probs, total, comps = np.zeros(len(self.class_names)), 0.0, {}
        if self.sk_names:
            x = self.features(roi)
            for k in self.sk_names:
                p = self.bundle["models"][k].predict_proba(x)[0]
                comps[k], probs, total = p, probs + self.weights[k] * p, total + self.weights[k]
        if FT_KEY in self.weights:
            xx = self._views(roi, 4)
            p = np.mean([torch.softmax(m(xx).float(), 1).mean(0).cpu().numpy() for m in self.ft_models], axis=0)
            comps[FT_KEY], probs, total = p, probs + self.weights[FT_KEY] * p, total + self.weights[FT_KEY]
        probs /= total
        i = int(probs.argmax())
        as_dict = lambda p: {c: round(float(v), 4) for c, v in zip(self.class_names, p)}
        return UndertoneResult(label=self.class_names[i], probs=as_dict(probs), confidence=float(probs[i]),
                               components={k: as_dict(v) for k, v in comps.items()},
                               ms=(time.perf_counter() - t0) * 1000)
