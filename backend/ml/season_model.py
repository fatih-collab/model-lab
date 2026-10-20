"""
Inferensi modul 12-Season — port dari notebook EXP-20261012-191927-3fc3:
    sel 3.3  parse_u8         (SegFormer face parsing)
    sel 4.1  embed_u8         (DINOv3 frozen: CLS + mean patch layer terakhir + mean patch layer 4 & 8, TTA flip)
    sel 7.1  ArmoNet, eval_tf (fine-tune multi-task, TTA flip)
    sel 10.2 predict_masked_image
Fungsi warna per region, pooling ensemble, temperature, dan himpunan konformal diambil langsung dari
ml.nb_generated.season_nb.

Model dilatih pada citra RGB-M Deep Armocromia (wajah + rambut, latar hitam). Kamera tidak menghasilkan itu,
jadi make_rgbm() membuatnya: crop wajah -> letterbox 512 -> face parsing -> piksel selain wajah/rambut dihitamkan.
"""
from __future__ import annotations

import copy
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image, ImageOps
from torchvision import transforms

from ml.nb_generated import season_nb as snb

# Label CelebAMask-HQ yang dipertahankan di citra RGB-M (wajah + rambut). Leher, baju, topi, latar -> hitam.
RGBM_KEEP_LABELS = ("skin", "nose", "eye_g", "l_eye", "r_eye", "l_brow", "r_brow", "l_ear", "r_ear", "ear_r",
                    "mouth", "u_lip", "l_lip", "hair")
CONFORMAL_ALPHA = 0.20          # himpunan kandidat yang memuat jawaban benar ~80% (rata-rata ~4 sub-season)


def letterbox(img: np.ndarray, size: int, resample=Image.BILINEAR) -> np.ndarray:
    """== ImageOps.pad(..., color=0) di load_squares(): persegi, rasio terjaga, latar hitam."""
    im = Image.fromarray(img)
    fill = 0 if im.mode == "L" else (0, 0, 0)
    return np.array(ImageOps.pad(im, (size, size), method=resample, color=fill))


class ArmoNet(nn.Module):
    """Identik dengan ArmoNet notebook (kunci state_dict sama), ukuran head dibaca dari bundle."""

    def __init__(self, backbone: nn.Module, n_classes: int, n_seasons: int, n_chars: int, dropout: float):
        super().__init__()
        self.backbone = backbone
        d = int(backbone.config.hidden_size)
        self.n_prefix = 1 + int(getattr(backbone.config, "num_register_tokens", 0))
        self.drop = nn.Dropout(dropout)
        self.head12 = nn.Linear(2 * d, n_classes)
        self.headS = nn.Linear(2 * d, n_seasons)
        self.headC = nn.Linear(2 * d, n_chars)
        self.headU = nn.Linear(2 * d, 2)

    def forward(self, x):
        h = self.backbone(pixel_values=x).last_hidden_state
        f = self.drop(torch.cat([h[:, 0], h[:, self.n_prefix:].mean(1)], dim=1))
        return self.head12(f), self.headS(f), self.headC(f), self.headU(f)


class SegformerParser:
    """== parse_u8(): batch uint8 (B, S, S, 3) -> label map uint8 (B, S, S)."""

    def __init__(self, model: nn.Module, device: str = "cpu"):
        self.model, self.device = model.float().to(device).eval(), device
        self.label_ids = {str(v): int(k) for k, v in model.config.id2label.items()}
        self._mean = torch.tensor(snb.IMNET_MEAN, device=device).view(1, 3, 1, 1)
        self._std = torch.tensor(snb.IMNET_STD, device=device).view(1, 3, 1, 1)

    @torch.no_grad()
    def __call__(self, batch_u8: np.ndarray) -> np.ndarray:
        x = torch.from_numpy(np.ascontiguousarray(batch_u8)).to(self.device).permute(0, 3, 1, 2).float() / 255.0
        x = (x - self._mean) / self._std
        logits = self.model(pixel_values=x).logits
        logits = F.interpolate(logits.float(), size=x.shape[-2:], mode="bilinear", align_corners=False)
        return logits.argmax(1).to(torch.uint8).cpu().numpy()


class FrozenEmbedder:
    """== embed_u8(): fitur DINOv3 frozen, rata-rata gambar asli + flip horizontal."""

    def __init__(self, model: nn.Module, img_size: int, extra_layers: list[int], device: str = "cpu"):
        self.model, self.img_size, self.extra_layers, self.device = model.float().to(device).eval(), img_size, extra_layers, device
        self.n_prefix = 1 + int(getattr(model.config, "num_register_tokens", 0))
        self._mean = torch.tensor(snb.IMNET_MEAN, device=device).view(1, 3, 1, 1)
        self._std = torch.tensor(snb.IMNET_STD, device=device).view(1, 3, 1, 1)

    @torch.no_grad()
    def __call__(self, batch_u8: np.ndarray) -> dict[str, np.ndarray]:
        x = torch.from_numpy(np.ascontiguousarray(batch_u8)).to(self.device).permute(0, 3, 1, 2).float() / 255.0
        if x.shape[-1] != self.img_size:
            x = F.interpolate(x, size=(self.img_size, self.img_size), mode="bilinear", antialias=True, align_corners=False)
        x = (x - self._mean) / self._std
        acc = None
        for xx in (x, torch.flip(x, dims=[3])):
            out = self.model(pixel_values=xx, output_hidden_states=True)
            last, hs = out.last_hidden_state, out.hidden_states
            f = {"cls_last": last[:, 0], "mean_last": last[:, self.n_prefix:].mean(1)}
            for li in self.extra_layers:
                f[f"mean_L{li}"] = hs[li][:, self.n_prefix:].mean(1)
            acc = f if acc is None else {k: acc[k] + f[k] for k in f}
        return {k: (v / 2).float().cpu().numpy() for k, v in acc.items()}


@dataclass
class SeasonResult:
    class_names: list[str]
    probs: np.ndarray                      # (12,) probabilitas terkalibrasi, urut class_names
    top: str
    confidence: float
    status: str                            # yakin | perlu_konfirmasi (ambang dari OOF notebook)
    candidates: list[str]                  # himpunan konformal ~80%
    p_warm: float                          # massa probabilitas Spring + Autumn
    components: dict[str, list[float]] = field(default_factory=dict)
    rgbm: np.ndarray | None = None         # citra RGB-M 256 px (debug)
    ms: float = 0.0


class SeasonModel:
    def __init__(self, bundle: dict, parse_fn: Callable[[np.ndarray], np.ndarray], label_ids: dict[str, int],
                 embedder: FrozenEmbedder | None, ft_models: list[nn.Module], device: str = "cpu"):
        self.b, self.parse, self.embedder, self.ft_models, self.device = bundle, parse_fn, embedder, ft_models, device
        self.class_names = list(bundle["class_names"])
        self.names = list(bundle["comp_names"])
        self.parse_size, self.cache_size = int(bundle["parse_size"]), int(bundle["cache_size"])
        self.region_ids = {r: [label_ids[n] for n in parts if n in label_ids] for r, parts in bundle["region_parts"].items()}
        self.glasses_ids = [label_ids[n] for n in ["eye_g"] if n in label_ids]
        self.keep_ids = [label_ids[n] for n in RGBM_KEEP_LABELS if n in label_ids]
        self.warm_mask = np.asarray(bundle["warm_of"]) == 1
        size = int(bundle["ft_img_size"])
        self.eval_tf = transforms.Compose([                     # == eval_tf notebook
            transforms.Resize((size, size), antialias=True), transforms.ToTensor(),
            transforms.Normalize(snb.IMNET_MEAN, snb.IMNET_STD)])
        need_emb = {"emb_lr", "emb_lr_orig"} & set(self.names)
        if need_emb and embedder is None:
            raise ValueError(f"Komponen {sorted(need_emb)} butuh backbone frozen.")
        if "ft" in self.names and not ft_models:
            raise ValueError("Komponen 'ft' aktif tetapi tidak ada checkpoint fine-tune yang dimuat.")

    @classmethod
    def load(cls, model_dir: Path, device: str = "cpu", max_folds: int = 0) -> "SeasonModel":
        import joblib
        from transformers import AutoModel, SegformerForSemanticSegmentation

        slim, raw = model_dir / "season_bundle.joblib", model_dir / "E12_artifacts.joblib"
        bundle = joblib.load(slim if slim.exists() else raw)
        parser = SegformerParser(SegformerForSemanticSegmentation.from_pretrained(bundle["parser"]), device)
        frozen = AutoModel.from_pretrained(bundle["backbone"]).float()
        embedder = FrozenEmbedder(frozen, int(bundle["emb_img_size"]), list(bundle["extra_mean_layers"]), device)
        ft = []
        if "ft" in bundle["comp_names"]:
            ckpts = bundle["ft_ckpts"][:max_folds] if max_folds else bundle["ft_ckpts"]
            for name in ckpts:
                ft.append(load_armonet(model_dir / name, copy.deepcopy(frozen), bundle, device))
        return cls(bundle, parser, parser.label_ids, embedder, ft, device)

    # ------------------------------------------------------------------------------------------------
    def make_rgbm(self, face_rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Crop wajah RGB -> (big 512 RGB-M, small 256 RGB-M, valid mask 512, small 256 RGB asli)."""
        big0 = letterbox(face_rgb, self.parse_size)
        keep = np.isin(self.parse(big0[None])[0], self.keep_ids)
        big = big0 * keep[..., None].astype(np.uint8)
        small = np.array(Image.fromarray(big).resize((self.cache_size, self.cache_size), Image.BILINEAR))
        small_orig = letterbox(face_rgb, self.cache_size)
        return big, small, keep, small_orig

    @torch.no_grad()
    def predict(self, face_rgb: np.ndarray) -> SeasonResult:
        t0 = time.perf_counter()
        big, small, valid, small_o = self.make_rgbm(face_rgb)
        label_map = self.parse(big[None])[0]                    # notebook mem-parsing citra RGB-M
        reg = snb.region_color_features(big, label_map, self.region_ids, self.glasses_ids, valid)[None, :]
        reg_keep = reg[:, self.b["reg_keep"]].astype(np.float64)

        comp = {}
        for name, img in (("emb_lr", small), ("emb_lr_orig", small_o)):
            if name in self.names:
                e = self.embedder(img[None])
                X = np.hstack([e[k] for k in self.b["emb_keys"]]).astype(np.float64)
                comp[name] = snb.proba_full(self.b["models"][name], X)
        if "color_hgb" in self.names:
            comp["color_hgb"] = snb.proba_full(self.b["models"]["color_hgb"], reg_keep)
        if "ft" in self.names:
            src = small_o if self.b.get("ft_input") == "original" else small
            x = self.eval_tf(Image.fromarray(src)).unsqueeze(0).to(self.device)
            ps = [((m(x)[0].float().softmax(1) + m(torch.flip(x, dims=[3]))[0].float().softmax(1)) / 2).cpu().numpy()
                  for m in self.ft_models]
            comp["ft"] = np.mean(ps, axis=0).astype(np.float64)

        p = snb.final_predict(comp, reg_keep, self.b)[0]
        order = np.argsort(-p)
        qhat = self.b["conformal_qhat"].get(CONFORMAL_ALPHA, self.b["conformal_qhat"][min(self.b["conformal_qhat"])])
        in_set = snb.conformal_sets(p[None], qhat)[0]
        return SeasonResult(
            class_names=self.class_names, probs=p, top=self.class_names[int(order[0])], confidence=float(p[order[0]]),
            status="yakin" if p[order[0]] >= self.b["conf_high"] else "perlu_konfirmasi",
            candidates=[self.class_names[int(i)] for i in order if in_set[i]],
            p_warm=float(p[self.warm_mask].sum()),
            components={k: np.round(v[0], 4).tolist() for k, v in comp.items()},
            rgbm=small, ms=(time.perf_counter() - t0) * 1000)


def load_armonet(path: Path, backbone: nn.Module, bundle: dict, device: str = "cpu") -> ArmoNet:
    m = ArmoNet(backbone, len(bundle["class_names"]), len(bundle["season_names"]), len(bundle["char_names"]),
                float(bundle["ft_dropout"]))
    m.load_state_dict(torch.load(path, map_location="cpu", weights_only=True))   # checkpoint fp16 -> param fp32
    return m.float().to(device).eval()
