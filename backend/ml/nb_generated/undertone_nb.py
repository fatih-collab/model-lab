# AUTO-GENERATED oleh backend/scripts/extract_models.py — JANGAN DIEDIT MANUAL.
# Sumber : Model/EXP-20261008-163613-7e87.ipynb
# sha256 : 19aebf9ae6b924f266da6b3abcffcd116c544c37268186e162c32d2180ab5a40
# Input  : foto bagian dalam pergelangan tangan (urat)
# Fungsi & konstanta diambil apa adanya dari sel notebook (+ dependensinya) agar inferensi
# identik dengan training. Regenerasi: python scripts/extract_models.py code

import math
import numpy as np
import cv2
from PIL import Image, ImageFilter, ImageOps
from sklearn.decomposition import PCA


# --- sel kode #1 ---
CLASS_NAMES     = ["cool", "neutral", "warm"]


# --- sel kode #1 ---
IMG_SIZE        = 224


# --- sel kode #1 ---
CACHE_MAX       = 512


# --- sel kode #1 ---
USE_ROI_CROP    = True


# --- sel kode #1 ---
N_TTA           = 8


# --- sel kode #3 ---
ROI_SIZE = 384


# --- sel kode #3 ---
def srgb_to_linear(x):
    return np.where(x > 0.04045, ((x + 0.055) / 1.055) ** 2.4, x / 12.92)


# --- sel kode #3 ---
def _rule_skin(rgb_u8):
    ycc = cv2.cvtColor(rgb_u8, cv2.COLOR_RGB2YCrCb)
    hsv = cv2.cvtColor(rgb_u8, cv2.COLOR_RGB2HSV)
    y, cr, cb = ycc[..., 0], ycc[..., 1], ycc[..., 2]
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    m1 = (cr >= 133) & (cr <= 180) & (cb >= 77) & (cb <= 135) & (y > 40)
    m2 = ((h <= 25) | (h >= 160)) & (s >= 15) & (s <= 200) & (v >= 50)
    return m1 | m2


# --- sel kode #3 ---
def skin_mask(rgb_u8):
    """
    Masker kulit adaptif (hanya MEMBACA warna):
    1) ambil warna kulit referensi dari area tengah (pergelangan biasanya di tengah)
    2) jarak Mahalanobis di ruang CIELab terhadap referensi tsb
    3) gabung dengan aturan YCrCb/HSV, ambil komponen terbesar yang menyentuh tengah
    """
    H, W = rgb_u8.shape[:2]
    lab = cv2.cvtColor(rgb_u8.astype(np.float32) / 255.0, cv2.COLOR_RGB2Lab)
    rule = _rule_skin(rgb_u8)
    cy0, cy1, cx0, cx1 = int(H * .3), int(H * .7), int(W * .3), int(W * .7)
    c_lab = lab[cy0:cy1, cx0:cx1].reshape(-1, 3)
    c_rule = rule[cy0:cy1, cx0:cx1].reshape(-1)
    ref = c_lab[c_rule] if c_rule.sum() > 200 else c_lab
    mu = np.median(ref, axis=0)
    cov = np.cov((ref - mu).T) + np.diag([4.0, 1.0, 1.0])
    inv = np.linalg.inv(cov)
    d = lab.reshape(-1, 3) - mu
    md = np.einsum("ij,jk,ik->i", d, inv, d).reshape(H, W)
    # Tekstur: kulit halus, motif latar (kayu/kain) bertekstur kuat
    L = lab[..., 0]
    mean = cv2.blur(L, (11, 11)); sq = cv2.blur(L * L, (11, 11))
    lstd = np.sqrt(np.maximum(sq - mean * mean, 0))
    tex_ref = np.median(lstd[cy0:cy1, cx0:cx1])
    smooth = lstd < max(5.0, 3.0 * tex_ref)
    m = (((md < 9.0) | (rule & (md < 25.0))) & smooth).astype(np.uint8)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, k)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k, iterations=2)
    n, lbl, stats, _ = cv2.connectedComponentsWithStats(m, 8)
    if n > 1:
        center_lbls = lbl[cy0:cy1, cx0:cx1]
        cand = [i for i in range(1, n) if (center_lbls == i).any()] or list(range(1, n))
        big = max(cand, key=lambda i: stats[i, cv2.CC_STAT_AREA])
        m = (lbl == big).astype(np.uint8)
    # isi lubang (urat gelap jangan sampai terbuang dari masker)
    cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    filled = np.zeros_like(m)
    cv2.drawContours(filled, cnts, -1, 1, thickness=-1)
    return filled.astype(bool)


# --- sel kode #3 ---
def crop_roi(img: Image.Image, margin=0.04, min_frac=0.10):
    """Crop ke bounding box kulit (lengan/pergelangan). Warna tidak diubah."""
    small = img.copy()
    small.thumbnail((ROI_SIZE, ROI_SIZE))
    m = skin_mask(np.asarray(small.convert("RGB")))
    if m.mean() < min_frac:
        return img
    ys, xs = np.where(m)
    H, W = m.shape
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    dy, dx = int((y1 - y0) * margin), int((x1 - x0) * margin)
    y0, y1 = max(0, y0 - dy), min(H, y1 + dy)
    x0, x1 = max(0, x0 - dx), min(W, x1 + dx)
    sx, sy = img.width / W, img.height / H
    return img.crop((int(x0 * sx), int(y0 * sy), int(x1 * sx), int(y1 * sy)))


# --- sel kode #3 ---
def dark_ridge(L, sigmas=(2.0, 3.5, 5.0)):
    """Vesselness sederhana (Hessian): respons tinggi pada garis GELAP memanjang (urat)."""
    out = np.zeros_like(L)
    for s in sigmas:
        g = cv2.GaussianBlur(L, (0, 0), s)
        dxx = cv2.Sobel(g, cv2.CV_32F, 2, 0, ksize=3)
        dyy = cv2.Sobel(g, cv2.CV_32F, 0, 2, ksize=3)
        dxy = cv2.Sobel(g, cv2.CV_32F, 1, 1, ksize=3)
        tmp = np.sqrt((dxx - dyy) ** 2 + 4 * dxy ** 2)
        l1 = 0.5 * (dxx + dyy + tmp)   # eigen terbesar: >0 untuk lembah (garis gelap)
        l2 = 0.5 * (dxx + dyy - tmp)
        rb = np.abs(l2) / (np.abs(l1) + 1e-6)          # bentuk memanjang -> rb kecil
        v = np.where(l1 > 0, l1 * np.exp(-rb ** 2 / 0.5), 0) * s ** 2
        out = np.maximum(out, v)
    return out


# --- sel kode #3 ---
def segment(img: Image.Image):
    """Return (rgb_u8, skin_interior, vein, skin_ref) masks pada resolusi kerja."""
    small = img.copy()
    small.thumbnail((ROI_SIZE, ROI_SIZE))
    rgb = np.asarray(small.convert("RGB"))
    m = skin_mask(rgb)
    if m.sum() < 800:
        m = np.ones(m.shape, bool)
    lab = cv2.cvtColor(rgb.astype(np.float32) / 255.0, cv2.COLOR_RGB2Lab)
    # Interior: buang tepi lengan (bayangan tepi sering terdeteksi sbg garis gelap)
    er_px = max(5, int(min(rgb.shape[:2]) * 0.06))
    interior = cv2.erode(m.astype(np.uint8), np.ones((er_px, er_px), np.uint8)).astype(bool)
    if interior.sum() < 500:
        interior = m
    L = lab[..., 0]
    ridge = dark_ridge(L) * interior
    # Piksel aneh (gelang, tato, bayangan pekat): terlalu gelap / warna jauh dari kulit
    ab_ref = np.median(lab[interior][:, 1:], axis=0)
    ab_dist = np.linalg.norm(lab[..., 1:] - ab_ref, axis=-1)
    L_ref = np.median(L[interior])
    plausible = interior & (ab_dist < 18) & (L > L_ref - 25)
    vals = ridge[plausible]
    thr = np.percentile(vals, 93) if vals.size else 0
    vein = plausible & (ridge >= thr) & (ridge > 0)
    vein = cv2.morphologyEx(vein.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8)).astype(bool)
    if vein.sum() < 30:
        vein = plausible & (ridge >= np.percentile(vals, 85)) if vals.size else interior
    # Kulit referensi: dekat urat tapi bukan urat (kontras lokal)
    near = cv2.dilate(vein.astype(np.uint8), np.ones((15, 15), np.uint8)).astype(bool)
    skin_ref = plausible & near & ~vein & (ridge < np.percentile(vals, 60) if vals.size else True)
    if skin_ref.sum() < 50:
        skin_ref = plausible & ~vein
    return rgb, lab, interior, vein, skin_ref


# --- sel kode #3 ---
def _stats(x):
    return [x.mean(), x.std(), *np.percentile(x, [10, 50, 90])]


# --- sel kode #3 ---
def color_features(img: Image.Image):
    """
    Fitur warna TERUKUR (gambar tidak diubah):
      A. Kulit (interior lengan): CIELab, HSV, YCrCb, ITA
      B. Urat vs kulit sekitarnya: dL, da*, db*, sudut hue, chroma,
         log-rasio RGB linear (illuminant-invariant / tahan white balance)
    """
    rgb, lab, interior, vein, skin_ref = segment(img)
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV).astype(np.float32)
    ycc = cv2.cvtColor(rgb, cv2.COLOR_RGB2YCrCb).astype(np.float32)
    lin = srgb_to_linear(rgb.astype(np.float32) / 255.0)

    feats, names = [], []
    def add(vals, prefix, labels):
        feats.extend(vals); names.extend([f"{prefix}_{l}" for l in labels])

    S = ["mean", "std", "p10", "p50", "p90"]
    sk = interior
    for ci, cn in enumerate(["L", "a", "b"]):
        add(_stats(lab[..., ci][sk]), f"skin_lab_{cn}", S)
    for ci, cn in enumerate(["S", "V"]):
        add(_stats(hsv[..., ci + 1][sk]), f"skin_hsv_{cn}", S)
    hue = hsv[..., 0][sk] * (2 * np.pi / 180)
    add([np.sin(hue).mean(), np.cos(hue).mean()], "skin_hue", ["sin", "cos"])
    for ci, cn in enumerate(["Cr", "Cb"]):
        add(_stats(ycc[..., ci + 1][sk]), f"skin_ycc_{cn}", S)
    Ls, a_s, bs = np.median(lab[sk], axis=0)
    add([math.degrees(math.atan2(Ls - 50, bs + 1e-6)),           # ITA
         math.degrees(math.atan2(bs, a_s)), math.hypot(a_s, bs)],   # hue angle & chroma kulit
        "skin", ["ITA", "hab", "Cab"])

    s_ref = np.median(lab[skin_ref], axis=0)
    v_med = np.median(lab[vein], axis=0)
    d = v_med - s_ref
    add(list(v_med), "vein_lab", ["L", "a", "b"])
    add(list(d), "delta_lab", ["L", "a", "b"])
    add([math.degrees(math.atan2(d[2], d[1])), math.hypot(d[1], d[2]),
         math.hypot(d[1], d[2]) / (abs(d[0]) + 1e-3),
         d[2] / (abs(d[0]) + 1e-3), d[1] / (abs(d[0]) + 1e-3)],
        "delta", ["hue_angle", "chroma", "chroma_per_dL", "db_per_dL", "da_per_dL"])

    lr = np.log(np.median(lin[vein], axis=0) + 1e-4) - np.log(np.median(lin[skin_ref], axis=0) + 1e-4)
    add(list(lr), "logratio", ["R", "G", "B"])
    add([lr[2] - lr[1], lr[0] - lr[1], lr[2] - lr[0]], "logratio", ["B_minus_G", "R_minus_G", "B_minus_R"])

    vh = hsv[..., 0][vein] * (2 * np.pi / 180)
    add([np.sin(vh).mean(), np.cos(vh).mean()], "vein_hue", ["sin", "cos"])
    add([vein.sum() / max(interior.sum(), 1), interior.mean()], "vein", ["frac", "skin_frac"])
    return np.nan_to_num(np.array(feats, np.float32)), names


# --- sel kode #3 ---
_UNSHARP = ImageFilter.UnsharpMask(radius=2, percent=120, threshold=3)


# --- sel kode #3 ---
def sharpen(img: Image.Image) -> Image.Image:
    return img.filter(_UNSHARP)


# --- sel kode #3 ---
def load_image(path, max_side=2048):
    img = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    img.thumbnail((max_side, max_side), Image.BICUBIC)
    return img


# --- sel kode #3 ---
def resize_short(img, s):
    w, h = img.size
    r = s / min(w, h)
    return img.resize((max(s, round(w * r)), max(s, round(h * r))), Image.BICUBIC)


# --- sel kode #3 ---
def center_crop(img, s):
    w, h = img.size
    l, t = (w - s) // 2, (h - s) // 2
    return img.crop((l, t, l + s, t + s))


# --- sel kode #3 ---
def tta_views(img, n=None):
    """View geometrik deterministik (tanpa ubah warna) -> fitur dirata-rata (stabil, anti-noise)."""
    n = n or N_TTA
    s = IMG_SIZE
    c = center_crop(resize_short(img, s), s)
    big = resize_short(img, int(s / 0.8))
    W, H = big.size
    views = [c, ImageOps.mirror(c), ImageOps.flip(c), center_crop(big, s),
             big.crop((0, 0, s, s)), big.crop((W - s, 0, W, s)),
             big.crop((0, H - s, s, H)), big.crop((W - s, H - s, W, H))]
    return [sharpen(v) for v in views[:n]]


# --- sel kode #7 ---
MEAN, STD = [0.485, 0.456, 0.406], [0.229, 0.224, 0.225]


# --- sel kode #8 ---
class SafePCA(PCA):
    """PCA yang otomatis membatasi n_components <= jumlah sampel (penting di fold/learning-curve kecil)."""
    def _clip(self, X):
        if isinstance(self.n_components, (int, np.integer)):
            self.n_components = int(min(self.n_components, X.shape[0] - 1, X.shape[1]))
    def fit(self, X, y=None):
        self._clip(X); return super().fit(X, y)
    def fit_transform(self, X, y=None):
        self._clip(X); return super().fit_transform(X, y)
