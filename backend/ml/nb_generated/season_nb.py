# AUTO-GENERATED oleh backend/scripts/extract_models.py — JANGAN DIEDIT MANUAL.
# Sumber : Model/armocromia_season_detection_v3.ipynb
# sha256 : a3a30871192e8f72578e008cdd6976da31332b35902484844563dbc2570fc22a
# Input  : crop wajah -> masker organ pyfacer FaRL -> RGB-M (wajah + rambut, latar hitam) + fitur warna per organ
# Fungsi & konstanta diambil apa adanya dari sel notebook (+ dependensinya) agar inferensi
# identik dengan training. Regenerasi: python scripts/extract_models.py code

import math
import os
import numpy as np
import cv2
import torch
import torch.nn as nn
import torch.nn.functional as F
import timm


# --- sel kode #0 ---
SMOKE = os.environ.get("ARMO_SMOKE", "0") == "1"


# --- sel kode #0 ---
CACHE_SIDE = 112 if SMOKE else 352


# --- sel kode #0 ---
PATCH = 64


# --- sel kode #0 ---
SEASONS = ["autunno", "estate", "inverno", "primavera"]


# --- sel kode #0 ---
SUBCLASSES = [("autunno", "deep"), ("autunno", "soft"), ("autunno", "warm"),
              ("estate", "cool"), ("estate", "light"), ("estate", "soft"),
              ("inverno", "bright"), ("inverno", "cool"), ("inverno", "deep"),
              ("primavera", "bright"), ("primavera", "light"), ("primavera", "warm")]


# --- sel kode #0 ---
SUB_NAMES = [f"{s}-{c}" for s, c in SUBCLASSES]


# --- sel kode #0 ---
NUM_SEASONS, NUM_CLASSES = len(SEASONS), len(SUBCLASSES)


# --- sel kode #0 ---
SUB2SEASON = np.array([SEASONS.index(s) for s, _ in SUBCLASSES])


# --- sel kode #0 ---
WARM_SEASONS = {SEASONS.index("autunno"), SEASONS.index("primavera")}


# --- sel kode #0 ---
PART_ID = {"bg": 0, "skin": 1, "hair": 2, "eye": 3, "brow": 4, "lip": 5, "nose": 6, "mouth": 7}


# --- sel kode #0 ---
N_PARTS = 8


# --- sel kode #0 ---
MODEL_ZOO = {
    "resnet50":   dict(family="CNN",   kind="cls",   backbone="resnet50.a1_in1k",                  img_size=320, batch=32, epochs=15, lr=2e-4, grad_ckpt=False),
    "effnetv2_s": dict(family="CNN",   kind="cls",   backbone="tf_efficientnetv2_s.in21k_ft_in1k", img_size=320, batch=32, epochs=15, lr=2e-4, grad_ckpt=False),
    "convnext_t": dict(family="CNN",   kind="cls",   backbone="convnext_tiny.fb_in22k_ft_in1k",    img_size=288, batch=32, epochs=15, lr=1e-4, grad_ckpt=True),
    "unet_r34":   dict(family="SEG",   kind="unet",  backbone="resnet34.a1_in1k",                  img_size=320, batch=24, epochs=15, lr=2e-4, grad_ckpt=False),
    "patch_attn": dict(family="PATCH", kind="patch", backbone="resnet18.a1_in1k",                  img_size=PATCH, batch=128, epochs=30, lr=3e-4, grad_ckpt=False),
}


# --- sel kode #0 ---
def season_probs(p12):
    return np.stack([p12[:, SUB2SEASON == s].sum(1) for s in range(NUM_SEASONS)], 1)


# --- sel kode #0 ---
def hierarchical_decode(p12):
    # P(season) = sum anak -> pilih season -> pilih sub terbaik di dalam season itu (konsisten 100%)
    ps = season_probs(p12)
    s_hat = ps.argmax(1)
    masked = np.where(SUB2SEASON[None, :] == s_hat[:, None], p12, -1)
    return s_hat, masked.argmax(1)


# --- sel kode #1 ---
LAPA2ID = {"background": 0, "face": 1, "rb": 4, "lb": 4, "re": 3, "le": 3, "nose": 6, "ulip": 5, "imouth": 7, "llip": 5, "hair": 2}


# --- sel kode #1 ---
def heuristic_labelmap(rgb):
    fg = rgb.max(-1) > 12
    ycc = cv2.cvtColor(rgb, cv2.COLOR_RGB2YCrCb)
    skin = fg & (ycc[..., 1] >= 135) & (ycc[..., 1] <= 180) & (ycc[..., 2] >= 85) & (ycc[..., 2] <= 135)
    skin = cv2.morphologyEx(skin.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)).astype(bool)
    lm = np.zeros(rgb.shape[:2], np.uint8)
    lm[skin] = 1
    if skin.any():
        ys = np.where(skin)[0]
        hair = fg & ~skin
        hair[int(np.percentile(ys, 60)):] = False
        lm[hair] = 2
    return lm


# --- sel kode #1 ---
REGIONS = ["skin", "hair", "eye", "lip", "brow"]


# --- sel kode #1 ---
def srgb_to_lab(rgb_u8):
    lab = cv2.cvtColor(rgb_u8.reshape(-1, 1, 3), cv2.COLOR_RGB2LAB).reshape(-1, 3).astype(np.float32)
    lab[:, 0] *= 100.0 / 255.0; lab[:, 1:] -= 128.0
    return lab


# --- sel kode #1 ---
def region_pixels(rgb, lm, region):
    m = lm == PART_ID[region]
    if region == "skin":
        m = cv2.erode(m.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    px = rgb[m]
    if len(px) < 20:
        return None, None
    lab = srgb_to_lab(px); L = lab[:, 0]
    if region == "skin":
        keep = (L >= 20) & (L <= 92)
        if keep.sum() >= 20:
            lo, hi = np.percentile(L[keep], [5, 95]); keep &= (L >= lo) & (L <= hi)
    elif region == "hair":
        keep = L <= np.percentile(L, 95)
    elif region == "eye":
        keep = L <= np.percentile(L, 60)          # buang sklera
    else:
        keep = np.ones(len(L), bool)
    return px[keep], lab[keep]


# --- sel kode #1 ---
def region_features(px, lab, pre, total):
    if px is None:
        return {}
    p = px.astype(np.float32); s = p.sum(1) + 1e-6
    hsv = cv2.cvtColor(px.reshape(-1, 1, 3), cv2.COLOR_RGB2HSV_FULL).reshape(-1, 3).astype(np.float32)
    hue = hsv[:, 0] / 255.0 * 2 * np.pi
    a, b = lab[:, 1].mean(), lab[:, 2].mean()
    return {f"{pre}_R": p[:, 0].mean(), f"{pre}_G": p[:, 1].mean(), f"{pre}_B": p[:, 2].mean(),
            f"{pre}_Rstd": p[:, 0].std(), f"{pre}_Gstd": p[:, 1].std(), f"{pre}_Bstd": p[:, 2].std(),
            f"{pre}_rratio": (p[:, 0] / s).mean(), f"{pre}_bratio": (p[:, 2] / s).mean(),
            f"{pre}_H": (np.degrees(np.arctan2(np.sin(hue).mean(), np.cos(hue).mean())) + 360) % 360,
            f"{pre}_S": hsv[:, 1].mean() / 255.0, f"{pre}_V": hsv[:, 2].mean() / 255.0, f"{pre}_Sstd": hsv[:, 1].std() / 255.0,
            f"{pre}_L": lab[:, 0].mean(), f"{pre}_a": a, f"{pre}_b": b, f"{pre}_Lstd": lab[:, 0].std(),
            f"{pre}_bstd": lab[:, 2].std(), f"{pre}_C": float(np.hypot(a, b)),
            f"{pre}_hab": float((np.degrees(np.arctan2(b, a)) + 360) % 360), f"{pre}_frac": len(px) / max(total, 1)}


# --- sel kode #1 ---
def extract_color_features(rgb, lm):
    fg = lm > 0; total = int(fg.sum()); f = {}
    for reg in REGIONS:
        f.update(region_features(*region_pixels(rgb, lm, reg), reg, total))
    px = rgb[fg].astype(np.float32) / 255.0
    if len(px):
        e = np.power(np.power(px, 6).mean(0), 1 / 6); e = e / (e.sum() + 1e-6)   # illuminant Shades-of-Gray
        f.update(illum_r=e[0], illum_g=e[1], illum_b=e[2])
    g = lambda k: f.get(k, np.nan)
    f["ITA"] = np.degrees(np.arctan2(g("skin_L") - 50, g("skin_b")))
    for reg in ["hair", "eye", "lip", "brow"]:
        f[f"dL_skin_{reg}"] = abs(g("skin_L") - g(f"{reg}_L"))
        f[f"db_skin_{reg}"] = g("skin_b") - g(f"{reg}_b")
        f[f"dE_skin_{reg}"] = np.sqrt((g("skin_L") - g(f"{reg}_L")) ** 2 + (g("skin_a") - g(f"{reg}_a")) ** 2 + (g("skin_b") - g(f"{reg}_b")) ** 2)
    f["michelson_skin_hair"] = (g("skin_L") - g("hair_L")) / (g("skin_L") + g("hair_L") + 1e-6)
    f["michelson_skin_eye"] = (g("skin_L") - g("eye_L")) / (g("skin_L") + g("eye_L") + 1e-6)
    c = [f["dL_skin_hair"], f["dL_skin_eye"], f["dL_skin_brow"]]
    f["contrast_max"] = np.nanmax(c) if np.isfinite(c).any() else np.nan
    cm = [g("skin_C"), g("hair_C"), g("eye_C")]
    f["chroma_mean"] = np.nanmean(cm) if np.isfinite(cm).any() else np.nan
    return f


# --- sel kode #1 ---
def crop_bbox(fg, h, w, margin=0.08):
    ys, xs = np.where(fg)
    if len(ys) < 50:
        return 0, h, 0, w
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    my, mx = int((y1 - y0) * margin), int((x1 - x0) * margin)
    return max(0, y0 - my), min(h, y1 + my), max(0, x0 - mx), min(w, x1 + mx)


# --- sel kode #1 ---
def letterbox(img, side, interp):
    h, w = img.shape[:2]; s = side / max(h, w)
    nh, nw = max(1, round(h * s)), max(1, round(w * s))
    r = cv2.resize(img, (nw, nh), interpolation=interp)
    out = np.zeros((side, side) + img.shape[2:], img.dtype)
    y0, x0 = (side - nh) // 2, (side - nw) // 2
    out[y0:y0 + nh, x0:x0 + nw] = r
    return out


# --- sel kode #2 ---
_M_BFD = np.array([[0.8951, 0.2664, -0.1614], [-0.7502, 1.7135, 0.0367], [0.0389, -0.0685, 1.0296]])


# --- sel kode #2 ---
_M_RGB2XYZ = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])


# --- sel kode #2 ---
def cct_to_xyz_white(T):
    x = (-4.6070e9 / T**3 + 2.9678e6 / T**2 + 0.09911e3 / T + 0.244063) if T <= 7000 else \
        (-2.0064e9 / T**3 + 1.9018e6 / T**2 + 0.24748e3 / T + 0.237040)
    y = -3.0 * x * x + 2.870 * x - 0.275
    return np.array([x / y, 1.0, (1 - x - y) / y])


# --- sel kode #2 ---
_W_D65 = cct_to_xyz_white(6504)


# --- sel kode #2 ---
def bradford_matrix(T):
    src, dst = _M_BFD @ _W_D65, _M_BFD @ cct_to_xyz_white(T)
    A = np.linalg.inv(_M_BFD) @ np.diag(dst / src) @ _M_BFD
    return np.linalg.inv(_M_RGB2XYZ) @ A @ _M_RGB2XYZ


# --- sel kode #2 ---
def _gauss_blur(img, sigma):
    rad = max(1, int(round(4 * sigma)))
    k = torch.arange(-rad, rad + 1, device=img.device, dtype=img.dtype)
    k = torch.exp(-k ** 2 / (2 * sigma ** 2)); k = k / k.sum()
    img = F.pad(img[None], (rad, rad, rad, rad), mode="reflect")
    img = F.conv2d(img, k.view(1, 1, 1, -1).expand(3, 1, 1, -1).contiguous(), groups=3)
    img = F.conv2d(img, k.view(1, 1, -1, 1).expand(3, 1, -1, 1).contiguous(), groups=3)
    return img[0]


# --- sel kode #2 ---
def gpu_aug(x_u8, m_u8, size, train):
    """x_u8: BxHxWx3 uint8 (GPU), m_u8: BxHxW labelmap atau None -> (Bx3xSxS float [0,1], BxSxS long)"""
    x = x_u8.permute(0, 3, 1, 2).float().div_(255.0)
    m = None if m_u8 is None else m_u8[:, None].float()
    if x.shape[-1] > size * 1.25:            # turunkan resolusi dulu (anti-aliasing) bila cache jauh lebih besar
        s0 = int(size * 1.1)
        x = F.interpolate(x, size=(s0, s0), mode="area")
        m = None if m is None else F.interpolate(m, size=(s0, s0), mode="nearest")
    if not train:
        x = F.interpolate(x, size=(size, size), mode="area")
        m = None if m is None else F.interpolate(m, size=(size, size), mode="nearest")[:, 0].long()
        return x, m
    B, dev = x.shape[0], x.device
    r = torch.empty(B, device=dev).uniform_(0.88, 1.0).sqrt()
    c = (torch.rand(B, 2, device=dev) * 2 - 1) * (1 - r)[:, None]
    flip = torch.where(torch.rand(B, device=dev) < 0.5, -1.0, 1.0)
    ang = torch.empty(B, device=dev).uniform_(-8, 8).deg2rad()
    t = torch.empty(B, 2, device=dev).uniform_(-0.04, 0.04) * 2
    cos, sin = ang.cos(), ang.sin()
    A = torch.stack([torch.stack([cos, sin], 1), torch.stack([-sin, cos], 1)], 1) * r[:, None, None]
    A[:, 0] *= flip[:, None]
    b = c - (A @ t[..., None])[..., 0]
    grid = F.affine_grid(torch.cat([A, b[..., None]], 2), (B, 3, size, size), align_corners=False)
    x = F.grid_sample(x, grid, mode="bilinear", padding_mode="zeros", align_corners=False)
    if m is not None:
        m = F.grid_sample(m, grid, mode="nearest", padding_mode="zeros", align_corners=False)[:, 0].long()
    sel = torch.rand(B) < 0.5                                           # Bradford ±250 K di linear sRGB
    if sel.any():
        M = torch.tensor(np.stack([bradford_matrix(6504 + np.random.uniform(-250, 250)) for _ in range(int(sel.sum()))]),
                         dtype=torch.float32, device=dev)
        sd = sel.to(dev); xs = x[sd]
        lin = torch.where(xs <= 0.04045, xs / 12.92, ((xs + 0.055) / 1.055) ** 2.4)
        lin = torch.einsum("bij,bjhw->bihw", M, lin).clamp(0, 1)
        x[sd] = torch.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin.clamp_min(1e-12) ** (1 / 2.4) - 0.055)
    sel = (torch.rand(B, device=dev) < 0.3)[:, None, None, None]        # kontras ±5%
    mu = x.mean((1, 2, 3), keepdim=True)
    x = torch.where(sel, (x - mu) * torch.empty(B, 1, 1, 1, device=dev).uniform_(0.95, 1.05) + mu, x)
    for j in torch.nonzero(torch.rand(B) < 0.2).flatten().tolist():    # blur
        x[j] = _gauss_blur(x[j], float(np.random.uniform(0.1, 0.8)))
    sel = (torch.rand(B, device=dev) < 0.2)[:, None, None, None]        # noise ISO
    x = torch.where(sel, x + torch.randn_like(x) * 0.01, x)
    return x.clamp_(0, 1), m


# --- sel kode #2 ---
class HierCls(nn.Module):
    """CNN (ResNet / EfficientNetV2 / ConvNeXt) dengan 2 head: season (4) + sub-season (12)."""
    def __init__(self, backbone, grad_ckpt=False, drop=0.3):
        super().__init__()
        self.backbone = timm.create_model(backbone, pretrained=True, num_classes=0)
        if grad_ckpt:
            self.backbone.set_grad_checkpointing(True)   # tukar compute dengan VRAM (~40% lebih hemat)
        d = self.backbone.num_features
        self.drop = nn.Dropout(drop)
        self.head_season, self.head_sub = nn.Linear(d, NUM_SEASONS), nn.Linear(d, NUM_CLASSES)

    def forward(self, x):
        h = self.drop(self.backbone(x))
        return self.head_season(h), self.head_sub(h), None


# --- sel kode #3 ---
def temp_scale(p, T):
    lg = np.log(np.clip(p, 1e-9, 1)) / T
    lg -= lg.max(1, keepdims=True); e = np.exp(lg)
    return e / e.sum(1, keepdims=True)
