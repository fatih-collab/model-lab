# AUTO-GENERATED oleh backend/scripts/extract_models.py — JANGAN DIEDIT MANUAL.
# Sumber : Model/EXP-20261012-191927-3fc3.ipynb
# sha256 : 0c72b49eddfb7ef663c4afd6ac183dcb16a2b85c04b10199f6834875e6499b5e
# Input  : foto wajah + rambut, latar dihitamkan (format RGB-M Deep Armocromia)
# Fungsi & konstanta diambil apa adanya dari sel notebook (+ dependensinya) agar inferensi
# identik dengan training. Regenerasi: python scripts/extract_models.py code

import numpy as np
from PIL import Image, ImageOps


# --- sel kode #0 ---
NUM_CLASSES = 12


# --- sel kode #0 ---
NUM_SEASONS = 4


# --- sel kode #0 ---
BACKBONE_HF_ID = "facebook/dinov3-vits16-pretrain-lvd1689m"


# --- sel kode #0 ---
EMB_IMG_SIZE = 224


# --- sel kode #0 ---
EXTRA_MEAN_LAYERS = [4, 8]


# --- sel kode #0 ---
PARSER_HF_ID = "jonathandinu/face-parsing"


# --- sel kode #0 ---
PARSE_SIZE = 512


# --- sel kode #0 ---
CACHE_SIZE = 256


# --- sel kode #0 ---
MASK_THRESH = 8 / 255


# --- sel kode #0 ---
FT_IMG_SIZE = 224


# --- sel kode #0 ---
FT_DROPOUT = 0.2


# --- sel kode #5 ---
WARM_SEASONS = {"autunno", "primavera"}


# --- sel kode #6 ---
def rgb2lab_np(rgb):
    rgb = np.asarray(rgb, dtype=np.float64)
    lin = np.where(rgb > 0.04045, ((rgb + 0.055) / 1.055) ** 2.4, rgb / 12.92)
    M = np.array([[0.4124564, 0.3575761, 0.1804375],
                  [0.2126729, 0.7151522, 0.0721750],
                  [0.0193339, 0.1191920, 0.9503041]])
    xyz = (lin @ M.T) / np.array([0.95047, 1.0, 1.08883])
    eps, kappa = 216 / 24389, 24389 / 27
    f = np.where(xyz > eps, np.cbrt(xyz), (kappa * xyz + 16) / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], axis=-1)


# --- sel kode #6 ---
REGION_PARTS = {                       # nama label CelebAMask-HQ per region
    "skin": ["skin", "nose"],
    "hair": ["hair"],
    "eye":  ["l_eye", "r_eye"],
    "lip":  ["u_lip", "l_lip"],
    "brow": ["l_brow", "r_brow"],
}


# --- sel kode #6 ---
REGION_MIN_PIX = {"skin": 400, "hair": 300, "eye": 20, "lip": 40, "brow": 30}


# --- sel kode #6 ---
BASE_STATS = ["L", "a", "b", "L_std", "chroma", "hue"]


# --- sel kode #6 ---
SKIN_EXTRA = ["a_std", "b_std", "L_p10", "L_p90", "ita"]


# --- sel kode #6 ---
CONTRASTS = ["dL_skin_hair", "dE_skin_hair", "dL_skin_eye", "dE_skin_eye", "dE_skin_lip", "da_lip_skin",
             "dL_skin_brow", "db_hair_skin", "L_range"]


# --- sel kode #6 ---
REGION_COLS = []


# --- sel kode #6 ---
for _r in REGION_PARTS:
    REGION_COLS += [f"{_r}_{s}" for s in BASE_STATS]


# --- sel kode #6 ---
REGION_COLS += [f"skin_{s}" for s in SKIN_EXTRA]


# --- sel kode #6 ---
REGION_COLS += [f"frac_{r}" for r in REGION_PARTS] + ["frac_glasses"]


# --- sel kode #6 ---
REGION_COLS += CONTRASTS + ["all_L", "all_a", "all_b"]


# --- sel kode #6 ---
COL_IX = {c: i for i, c in enumerate(REGION_COLS)}


# --- sel kode #6 ---
def region_color_features(img_u8, label_map, region_ids, glasses_ids=(), valid=None):
    # img_u8: (H,W,3) uint8 ; label_map: (H,W) int ; region_ids: {region: [id label]}
    out = np.full(len(REGION_COLS), np.nan)
    if valid is None:                                   # tanpa mask biner: piksel hitam dianggap latar
        valid = img_u8.max(axis=2) > int(MASK_THRESH * 255)
    n_valid = int(valid.sum())
    if n_valid < 200:
        return out
    lab_all = rgb2lab_np(img_u8[valid].astype(np.float32) / 255.0)
    out[[COL_IX["all_L"], COL_IX["all_a"], COL_IX["all_b"]]] = np.median(lab_all, axis=0)
    lm_valid = label_map[valid]

    med = {}
    for r, ids in region_ids.items():
        m = np.isin(lm_valid, ids)
        n = int(m.sum())
        out[COL_IX[f"frac_{r}"]] = n / n_valid
        if n < REGION_MIN_PIX[r]:
            continue
        lab = lab_all[m]
        if r == "skin":                                   # buang bayangan dan highlight ekstrem
            lo, hi = np.percentile(lab[:, 0], [10, 90])
            keep = (lab[:, 0] >= lo) & (lab[:, 0] <= hi)
            if keep.sum() >= REGION_MIN_PIX[r] // 2:
                lab = lab[keep]
        md = np.median(lab, axis=0)
        med[r] = md
        out[COL_IX[f"{r}_L"]], out[COL_IX[f"{r}_a"]], out[COL_IX[f"{r}_b"]] = md
        out[COL_IX[f"{r}_L_std"]] = lab[:, 0].std()
        out[COL_IX[f"{r}_chroma"]] = np.median(np.hypot(lab[:, 1], lab[:, 2]))
        out[COL_IX[f"{r}_hue"]] = np.degrees(np.arctan2(md[2], md[1]))
        if r == "skin":
            out[COL_IX["skin_a_std"]], out[COL_IX["skin_b_std"]] = lab[:, 1].std(), lab[:, 2].std()
            out[COL_IX["skin_L_p10"]], out[COL_IX["skin_L_p90"]] = np.percentile(lab[:, 0], [10, 90])
            out[COL_IX["skin_ita"]] = np.degrees(np.arctan2(md[0] - 50.0, md[2]))
    out[COL_IX["frac_glasses"]] = float(np.isin(lm_valid, list(glasses_ids)).sum()) / n_valid if len(glasses_ids) else 0.0

    def dE(x, y):
        return float(np.linalg.norm(med[x] - med[y]))
    if "skin" in med and "hair" in med:
        out[COL_IX["dL_skin_hair"]] = med["skin"][0] - med["hair"][0]
        out[COL_IX["dE_skin_hair"]] = dE("skin", "hair")
        out[COL_IX["db_hair_skin"]] = med["hair"][2] - med["skin"][2]
    if "skin" in med and "eye" in med:
        out[COL_IX["dL_skin_eye"]] = med["skin"][0] - med["eye"][0]
        out[COL_IX["dE_skin_eye"]] = dE("skin", "eye")
    if "skin" in med and "lip" in med:
        out[COL_IX["dE_skin_lip"]] = dE("skin", "lip")
        out[COL_IX["da_lip_skin"]] = med["lip"][1] - med["skin"][1]
    if "skin" in med and "brow" in med:
        out[COL_IX["dL_skin_brow"]] = med["skin"][0] - med["brow"][0]
    Ls = [med[r][0] for r in ("skin", "hair", "eye") if r in med]
    if len(Ls) >= 2:
        out[COL_IX["L_range"]] = max(Ls) - min(Ls)
    return out


# --- sel kode #6 ---
def load_squares(path, mask_path=None, orig_path=None):
    # Letterbox ke persegi (latar hitam, rasio wajah terjaga).
    # Keluaran: RGB-M (PARSE_SIZE), RGB-M (CACHE_SIZE), piksel valid (PARSE_SIZE, bool), RGB asli (CACHE_SIZE)
    with Image.open(path) as im:
        im = im.convert("RGB")
        base_size = im.size
        sq = ImageOps.pad(im, (PARSE_SIZE, PARSE_SIZE), method=Image.BILINEAR, color=(0, 0, 0))
    big = np.array(sq, dtype=np.uint8)
    small = np.array(sq.resize((CACHE_SIZE, CACHE_SIZE), Image.BILINEAR), dtype=np.uint8)
    valid = big.max(axis=2) > int(MASK_THRESH * 255)
    if mask_path is not None:
        with Image.open(mask_path) as mk:
            mk = mk.convert("L")
            if mk.size != base_size:
                mk = mk.resize(base_size, Image.NEAREST)
            arr = np.array(ImageOps.pad(mk, (PARSE_SIZE, PARSE_SIZE), method=Image.NEAREST, color=0))
        valid = arr > (arr.max() / 2.0) if arr.max() > 0 else valid
    small_o = np.zeros((1, 1, 3), dtype=np.uint8)
    if orig_path is not None:
        with Image.open(orig_path) as og:
            og = og.convert("RGB")
            if og.size != base_size:
                og = og.resize(base_size, Image.BILINEAR)
            small_o = np.array(ImageOps.pad(og, (CACHE_SIZE, CACHE_SIZE), method=Image.BILINEAR, color=(0, 0, 0)), dtype=np.uint8)
    return big, small, valid, small_o


# --- sel kode #8 ---
IMNET_MEAN, IMNET_STD = (0.485, 0.456, 0.406), (0.229, 0.224, 0.225)


# --- sel kode #14 ---
def apply_temperature(p, T):
    z = np.log(np.clip(p, 1e-12, 1.0)) / float(T)
    z -= z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


# --- sel kode #14 ---
def pool(prob_list, weights):
    # log-linear pooling (rata-rata geometrik berbobot), dinormalisasi ulang
    z = sum(w * np.log(np.clip(p, 1e-12, 1.0)) for p, w in zip(prob_list, weights))
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


# --- sel kode #14 ---
def proba_full(model, X, n_classes=NUM_CLASSES):
    p = model.predict_proba(X)
    out = np.zeros((len(X), n_classes))
    out[:, model.classes_] = p
    return out


# --- sel kode #18 ---
def stack_features(comp, reg_rows, names):
    # masukan penggabung: log-probabilitas tiap komponen + fitur warna per region
    return np.hstack([np.log(np.clip(comp[n], 1e-6, 1.0)) for n in names] + [reg_rows]).astype(np.float32)


# --- sel kode #18 ---
def final_predict(comp, reg_rows, cfg):
    # satu-satunya jalur dari prediksi komponen -> probabilitas akhir (dipakai OOF, holdout, test, dan inferensi)
    if cfg["method"] == "xgb_stack":
        raw = np.asarray(cfg["stacker"].predict_proba(stack_features(comp, reg_rows, cfg["comp_names"])), dtype=np.float64)
    else:
        raw = pool([apply_temperature(comp[n], cfg["comp_temps"][n]) for n in cfg["comp_names"]], cfg["ens_weights"])
    return apply_temperature(raw, cfg["temperature"])


# --- sel kode #20 ---
def conformal_sets(p, qhat):
    S = p >= (1.0 - qhat)
    S[np.arange(len(p)), p.argmax(1)] = True          # prediksi teratas selalu masuk
    return S
