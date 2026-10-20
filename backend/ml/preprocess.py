"""
Fase 1 — Preprocessing frame kamera sebelum inferensi.

Alur WAJAH (modul 12-season):
    decode -> deteksi wajah -> Gray-World WB -> luruskan kemiringan -> crop wajah + rambut -> quality gate
Alur PERGELANGAN (modul undertone — model dilatih pada foto urat pergelangan, bukan wajah):
    decode -> masker kulit (fungsi notebook) -> Gray-World WB -> crop_roi() (fungsi notebook) -> quality gate

Catatan Gray-World:
    Asumsinya rata-rata warna SCENE = abu-abu. Pada crop wajah yang ketat rata-ratanya adalah warna kulit, sehingga
    WB justru menetralkan undertone (sinyal yang mau diukur). Karena itu gain DIESTIMASI dari area di luar
    wajah/kulit (latar, baju) lalu DITERAPKAN ke seluruh frame termasuk wajah. Gain dihitung di ruang RGB linear
    dan dibatasi (clip) supaya dinding/baju berwarna mencolok tidak merusak hasil.

Masking latar (format RGB-M dataset) butuh model face-parsing, jadi dilakukan di Fase 2 bersama inferensi season.

CLI uji cepat:
    python -m ml.preprocess foto.jpg --kind face --out crop.png
"""
from __future__ import annotations

import base64
import binascii
import io
import math
import threading
from dataclasses import asdict, dataclass, field
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

MODELS_DIR = Path(__file__).resolve().parents[1] / "models"
YUNET_PATH = MODELS_DIR / "face_detection_yunet_2023mar.onnx"

ISSUE_MESSAGES = {
    # blocking: frame tidak dikirim ke model
    "no_face": "Wajah tidak terdeteksi. Hadapkan wajah ke kamera.",
    "face_too_small": "Wajah terlalu jauh. Dekatkan wajah ke kamera.",
    "too_dark": "Pencahayaan terlalu gelap. Cari cahaya yang lebih terang (idealnya cahaya alami).",
    "overexposed": "Gambar terlalu terang / silau. Hindari cahaya langsung ke kamera.",
    "no_wrist": "Pergelangan tidak terdeteksi. Arahkan bagian dalam pergelangan ke area panduan.",
    "face_instead_of_wrist": "Yang terlihat adalah wajah. Arahkan bagian dalam pergelangan tangan.",
    "blurry": "Gambar buram. Tahan kamera / tangan tetap diam.",
    # warning: tetap diproses, ditampilkan sebagai saran
    "multiple_faces": "Terdeteksi lebih dari satu wajah; yang terbesar dipakai.",
    "strong_color_cast": "Cahaya ruangan sangat berwarna; hasil bisa kurang akurat.",
    "face_near_edge": "Wajah terlalu dekat ke tepi frame; posisikan di tengah.",
    "wb_fallback": "Latar terlalu sempit untuk koreksi cahaya; koreksi memakai seluruh frame.",
}


# =====================================================================================================
# Decode
# =====================================================================================================
class ImageDecodeError(ValueError):
    pass


def decode_image(data: bytes | str, max_side: int = 1280) -> np.ndarray:
    """JPEG/PNG/WebP (bytes, base64, atau data URL) -> BGR uint8. Orientasi EXIF diperbaiki, sisi terpanjang dibatasi."""
    if isinstance(data, str):
        s = data.strip()
        if s.startswith("data:"):
            s = s.split(",", 1)[-1]
        try:
            data = base64.b64decode(s, validate=True)
        except (binascii.Error, ValueError) as e:
            raise ImageDecodeError("String base64 tidak valid.") from e
    try:
        with Image.open(io.BytesIO(data)) as im:
            rgb = np.asarray(ImageOps.exif_transpose(im).convert("RGB"))
    except (OSError, Image.DecompressionBombError) as e:
        raise ImageDecodeError(f"Gambar tidak bisa dibaca: {e}") from e
    return resize_max_side(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR), max_side)


def resize_max_side(img: np.ndarray, max_side: int, interpolation: int = cv2.INTER_AREA) -> np.ndarray:
    h, w = img.shape[:2]
    s = max_side / max(h, w)
    if s >= 1.0:
        return img
    return cv2.resize(img, (max(1, round(w * s)), max(1, round(h * s))), interpolation=interpolation)


# =====================================================================================================
# Gray-World White Balance (RGB linear, gain dari area referensi)
# =====================================================================================================
_V = np.arange(256, dtype=np.float64) / 255.0
_SRGB_TO_LINEAR = np.where(_V > 0.04045, ((_V + 0.055) / 1.055) ** 2.4, _V / 12.92).astype(np.float32)


def _linear_to_srgb_u8(lin: np.ndarray) -> np.ndarray:
    lin = np.clip(lin, 0.0, 1.0)
    srgb = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.power(lin, 1 / 2.4) - 0.055)
    return np.clip(srgb * 255.0 + 0.5, 0, 255).astype(np.uint8)


@dataclass
class WhiteBalanceInfo:
    gains_bgr: tuple[float, float, float] = (1.0, 1.0, 1.0)
    source: str = "none"            # background | full_frame | none | disabled
    ref_fraction: float = 0.0       # porsi frame yang dipakai sebagai referensi abu-abu
    neutral_fraction: float = 0.0   # porsi referensi yang dianggap netral pada iterasi terakhir
    clipped: bool = False           # gain menyentuh batas -> cast warna sangat kuat


def estimate_gray_world_gains(bgr: np.ndarray, exclude_mask: np.ndarray | None = None, *,
                              clip: tuple[float, float] = (0.67, 1.5), min_ref_fraction: float = 0.05,
                              max_side: int = 256, neutral_sat: float = 0.35, iters: int = 4) -> WhiteBalanceInfo:
    """
    Gain per kanal (B, G, R) agar rata-rata area referensi menjadi abu-abu netral.
    exclude_mask (bool, ukuran bebas) menandai piksel yang TIDAK boleh jadi referensi (wajah, rambut, kulit).
    Bila area sisa < min_ref_fraction frame, referensi kembali ke seluruh frame.

    Gray-World murni gagal bila latar berisi benda berwarna (baju oranye, dinding merah). Karena itu rata-rata
    dihitung iteratif hanya dari piksel yang (setelah koreksi sementara) mendekati netral, dengan ambang saturasi
    linear yang mengetat dari 0.6 ke neutral_sat. Pada scene netral hasilnya sama dengan Gray-World biasa; bila
    tak ada piksel netral sama sekali, kembali ke Gray-World murni.
    """
    small = resize_max_side(bgr, max_side)
    usable = (small.max(axis=2) < 250) & (small.min(axis=2) > 8)          # buang piksel jenuh / hampir hitam
    ref, source = usable, "full_frame"
    if exclude_mask is not None:
        ex = cv2.resize(exclude_mask.astype(np.uint8), (small.shape[1], small.shape[0]),
                        interpolation=cv2.INTER_NEAREST).astype(bool)
        bg = usable & ~ex
        if bg.mean() >= min_ref_fraction:
            ref, source = bg, "background"
    if ref.sum() < 64:
        return WhiteBalanceInfo()
    px = _SRGB_TO_LINEAR[small[ref]]                                    # (N, 3) linear B, G, R
    raw, neutral = np.ones(3, np.float32), 0.0
    for thr in np.linspace(0.6, neutral_sat, iters):                    # ambang saturasi makin ketat
        c = px * raw
        sel = (c.max(axis=1) - c.min(axis=1)) / (c.max(axis=1) + 1e-6) < thr
        if sel.sum() < max(64, 0.02 * usable.size):
            break
        means, neutral = px[sel].mean(axis=0), float(sel.mean())
        raw = means.mean() / np.maximum(means, 1e-6)
    if neutral == 0.0:                                                  # tak ada piksel netral: Gray-World murni
        means = px.mean(axis=0)
        raw = means.mean() / np.maximum(means, 1e-6)
    gains = np.clip(raw, *clip)
    return WhiteBalanceInfo(tuple(float(g) for g in gains), source, float(ref.mean()), neutral,
                            bool(np.any(np.abs(gains - raw) > 1e-6)))


def apply_white_balance(bgr: np.ndarray, gains_bgr, strength: float = 1.0) -> np.ndarray:
    """Terapkan gain di ruang linear via LUT 256 entri per kanal (cepat untuk frame real-time)."""
    g = np.power(np.asarray(gains_bgr, dtype=np.float32), strength)
    if np.allclose(g, 1.0):
        return bgr
    lut = np.stack([_linear_to_srgb_u8(_SRGB_TO_LINEAR * gc) for gc in g], axis=-1)    # (256, 3)
    return cv2.LUT(bgr, lut.reshape(256, 1, 3))


def gray_world_white_balance(bgr: np.ndarray, exclude_mask: np.ndarray | None = None,
                             strength: float = 1.0, **kw) -> tuple[np.ndarray, WhiteBalanceInfo]:
    info = estimate_gray_world_gains(bgr, exclude_mask, **kw)
    return apply_white_balance(bgr, info.gains_bgr, strength), info


# =====================================================================================================
# Deteksi wajah: YuNet (OpenCV DNN) -> fallback Haar; MTCNN opsional
# =====================================================================================================
@dataclass
class FaceBox:
    x: float
    y: float
    w: float
    h: float
    score: float = 1.0
    eyes: tuple[tuple[float, float], tuple[float, float]] | None = None    # (mata kiri-gambar, mata kanan-gambar)

    @property
    def area(self) -> float:
        return self.w * self.h

    @property
    def center(self) -> tuple[float, float]:
        return self.x + self.w / 2, self.y + self.h / 2

    def scaled(self, s: float) -> "FaceBox":
        eyes = tuple((ex * s, ey * s) for ex, ey in self.eyes) if self.eyes else None
        return FaceBox(self.x * s, self.y * s, self.w * s, self.h * s, self.score, eyes)


class FaceDetector:
    """backend: 'auto' (YuNet bila file model ada, selain itu Haar), 'yunet', 'haar', atau 'mtcnn'."""

    def __init__(self, backend: str = "auto", yunet_model: str | Path = YUNET_PATH,
                 score_threshold: float = 0.75, detect_max_side: int | None = None):
        if backend == "auto":
            backend = "yunet" if Path(yunet_model).exists() else "haar"
        if detect_max_side is None:              # Haar jauh lebih lambat; wajah selfie cukup besar untuk 400 px
            detect_max_side = 400 if backend == "haar" else 640
        self.backend, self.score_threshold, self.detect_max_side = backend, score_threshold, detect_max_side
        self._lock = threading.Lock()           # FaceDetectorYN / CascadeClassifier tidak thread-safe
        if backend == "yunet":
            self._yunet = cv2.FaceDetectorYN.create(str(yunet_model), "", (320, 320), score_threshold, 0.3, 50)
        elif backend == "haar":
            # alt2: lebih tahan poni / wajah sedikit menoleh dan lebih sedikit deteksi palsu dibanding "default"
            self._haar = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_alt2.xml")
            if self._haar.empty():
                raise RuntimeError("Haar cascade OpenCV tidak ditemukan.")
        elif backend == "mtcnn":
            from facenet_pytorch import MTCNN
            self._mtcnn = MTCNN(keep_all=True, device="cpu")
        else:
            raise ValueError(f"backend tidak dikenal: {backend}")

    def detect(self, bgr: np.ndarray) -> list[FaceBox]:
        """Semua wajah, terurut dari yang terbesar. Koordinat pada frame masukan."""
        small = resize_max_side(bgr, self.detect_max_side)
        s = bgr.shape[1] / small.shape[1]
        with self._lock:
            faces = getattr(self, f"_detect_{self.backend}")(small)
        return sorted((f.scaled(s) for f in faces), key=lambda f: f.area, reverse=True)

    def _detect_yunet(self, bgr):
        h, w = bgr.shape[:2]
        self._yunet.setInputSize((w, h))
        _, faces = self._yunet.detect(bgr)
        out = []
        for f in faces if faces is not None else []:
            eyes = tuple(sorted([(float(f[4]), float(f[5])), (float(f[6]), float(f[7]))]))
            out.append(FaceBox(*map(float, f[:4]), score=float(f[14]), eyes=eyes))
        return out

    def _detect_haar(self, bgr):
        gray = cv2.equalizeHist(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY))
        m = max(24, int(0.08 * min(gray.shape)))
        rects = self._haar.detectMultiScale(gray, scaleFactor=1.15, minNeighbors=4, minSize=(m, m))
        return [FaceBox(float(x), float(y), float(w), float(h)) for x, y, w, h in rects]

    def _detect_mtcnn(self, bgr):
        boxes, probs, points = self._mtcnn.detect(Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)), landmarks=True)
        if boxes is None:
            return []
        out = []
        for (x0, y0, x1, y1), p, pt in zip(boxes, probs, points):
            if p >= self.score_threshold:
                eyes = tuple(sorted([tuple(map(float, pt[0])), tuple(map(float, pt[1]))]))
                out.append(FaceBox(float(x0), float(y0), float(x1 - x0), float(y1 - y0), float(p), eyes))
        return out


# =====================================================================================================
# Preprocessor
# =====================================================================================================
@dataclass(frozen=True)
class PreprocessConfig:
    white_balance: bool = True
    wb_strength: float = 1.0                  # 0 = mati, 1 = Gray-World penuh
    wb_clip: tuple[float, float] = (0.67, 1.5)
    align_face: bool = True                   # luruskan roll kepala dari landmark mata (YuNet/MTCNN)
    max_align_deg: float = 25.0
    # Framing crop relatif terhadap box detektor; meniru dataset Deep Armocromia (wajah + rambut).
    crop_width_scale: float = 1.9
    crop_top: float = 0.7
    crop_bottom: float = 0.35
    min_face_frac: float = 0.12               # lebar wajah minimal relatif sisi pendek frame
    min_brightness: float = 0.25              # L rata-rata area kulit (0..1)
    max_brightness: float = 0.92
    min_sharpness: float = 30.0               # variansi Laplacian (gambar 256 px)
    edge_cut_frac: float = 0.15               # porsi crop yang terpotong tepi frame sebelum diberi warning


@dataclass
class PreprocessResult:
    ok: bool
    kind: str                                         # face | wrist
    image_rgb: np.ndarray | None = None               # crop siap model (RGB uint8)
    box: list[float] | None = None                    # box wajah (x, y, w, h) pada frame asli -> posisi cincin palet
    crop_box: list[int] | None = None                 # (x0, y0, x1, y1) area crop pada frame asli
    frame_size: tuple[int, int] = (0, 0)              # (w, h)
    wb: WhiteBalanceInfo = field(default_factory=WhiteBalanceInfo)
    issues: list[str] = field(default_factory=list)   # blocking
    warnings: list[str] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)

    def meta(self) -> dict:
        """Ringkasan JSON-serializable (tanpa piksel) untuk respons API / log."""
        return {
            "ok": self.ok, "kind": self.kind, "box": self.box, "crop_box": self.crop_box,
            "frame_size": list(self.frame_size), "white_balance": asdict(self.wb),
            "issues": self.issues, "warnings": self.warnings,
            "messages": [ISSUE_MESSAGES[c] for c in self.issues + self.warnings if c in ISSUE_MESSAGES],
            "metrics": {k: round(float(v), 4) for k, v in self.metrics.items()},
        }


def _exposure_and_sharpness(bgr: np.ndarray) -> tuple[float, float]:
    region = resize_max_side(bgr, 256)
    brightness = float(cv2.cvtColor(region, cv2.COLOR_BGR2LAB)[..., 0].mean() / 255.0)
    sharpness = float(cv2.Laplacian(cv2.cvtColor(region, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var())
    return brightness, sharpness


class Preprocessor:
    def __init__(self, config: PreprocessConfig | None = None, detector: FaceDetector | None = None):
        self.cfg = config or PreprocessConfig()
        self._detector = detector

    @property
    def detector(self) -> FaceDetector:
        if self._detector is None:
            self._detector = FaceDetector()
        return self._detector

    # ------------------------------------------------------------------------------------- wajah
    def process_face(self, bgr: np.ndarray) -> PreprocessResult:
        cfg = self.cfg
        H, W = bgr.shape[:2]
        res = PreprocessResult(ok=False, kind="face", frame_size=(W, H))
        faces = self.detector.detect(bgr)
        if not faces:
            res.issues.append("no_face")
            return res
        face = faces[0]
        if len(faces) > 1 and faces[1].area > 0.3 * face.area:
            res.warnings.append("multiple_faces")
        res.box = [round(v, 1) for v in (face.x, face.y, face.w, face.h)]
        res.metrics["face_frac"] = face.w / min(H, W)
        if res.metrics["face_frac"] < cfg.min_face_frac:
            res.issues.append("face_too_small")

        x0, y0, x1, y1, cut = self._face_crop_box(face, W, H)
        res.crop_box = [x0, y0, x1, y1]
        if cut > cfg.edge_cut_frac:
            res.warnings.append("face_near_edge")

        # Referensi WB = semua kecuali area crop (wajah + rambut) dan kolom leher/dada di bawahnya.
        work = bgr
        if cfg.white_balance:
            exclude = np.zeros((H, W), dtype=bool)
            exclude[y0:y1, x0:x1] = True
            cx = face.x + face.w / 2
            exclude[int(face.y + face.h):, max(0, int(cx - 0.75 * face.w)):int(cx + 0.75 * face.w)] = True
            res.wb = estimate_gray_world_gains(bgr, exclude, clip=cfg.wb_clip)
            work = apply_white_balance(bgr, res.wb.gains_bgr, cfg.wb_strength)
            self._wb_warnings(res)
        else:
            res.wb = WhiteBalanceInfo(source="disabled")

        if cfg.align_face and face.eyes:
            (lx, ly), (rx, ry) = face.eyes
            angle = math.degrees(math.atan2(ry - ly, rx - lx))
            res.metrics["roll_deg"] = angle
            if 1.5 < abs(angle) <= cfg.max_align_deg:
                M = cv2.getRotationMatrix2D(face.center, angle, 1.0)
                work = cv2.warpAffine(work, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

        # Kualitas diukur di bagian dalam wajah (60% tengah box) setelah WB.
        ix0, iy0 = int(face.x + 0.2 * face.w), int(face.y + 0.2 * face.h)
        ix1, iy1 = int(face.x + 0.8 * face.w), int(face.y + 0.8 * face.h)
        inner = work[max(0, iy0):max(1, iy1), max(0, ix0):max(1, ix1)]
        if inner.size:
            b, s = _exposure_and_sharpness(inner)
            res.metrics.update(brightness=b, sharpness=s)
            if b < cfg.min_brightness:
                res.issues.append("too_dark")
            elif b > cfg.max_brightness:
                res.issues.append("overexposed")
            if s < cfg.min_sharpness:
                res.warnings.append("blurry")          # warna tetap terbaca walau sedikit buram

        res.image_rgb = cv2.cvtColor(work[y0:y1, x0:x1], cv2.COLOR_BGR2RGB)
        res.ok = not res.issues
        return res

    def _face_crop_box(self, f: FaceBox, W: int, H: int) -> tuple[int, int, int, int, float]:
        cfg = self.cfg
        cx = f.x + f.w / 2
        half = f.w * cfg.crop_width_scale / 2
        want = (cx - half, f.y - cfg.crop_top * f.h, cx + half, f.y + (1 + cfg.crop_bottom) * f.h)
        x0, y0 = max(0, int(round(want[0]))), max(0, int(round(want[1])))
        x1, y1 = min(W, int(round(want[2]))), min(H, int(round(want[3])))
        want_area = (want[2] - want[0]) * (want[3] - want[1])
        cut = 1.0 - (x1 - x0) * (y1 - y0) / max(want_area, 1.0)
        return x0, y0, x1, y1, cut

    # ------------------------------------------------------------------------------- pergelangan
    def process_wrist(self, bgr: np.ndarray) -> PreprocessResult:
        from ml.nb_generated import undertone_nb as unb

        cfg = self.cfg
        H, W = bgr.shape[:2]
        res = PreprocessResult(ok=False, kind="wrist", frame_size=(W, H))

        faces = self.detector.detect(bgr)
        if faces and faces[0].w / min(H, W) > 0.25:
            res.issues.append("face_instead_of_wrist")
            return res

        small_rgb = cv2.cvtColor(resize_max_side(bgr, unb.ROI_SIZE), cv2.COLOR_BGR2RGB)
        skin = unb.skin_mask(small_rgb)
        # skin_mask adaptif (referensi = warna tengah frame), jadi dinding polos pun lolos. Syaratkan sebagian
        # besar piksel mask juga memenuhi aturan warna kulit YCrCb/HSV.
        rule_frac = float(unb._rule_skin(small_rgb)[skin].mean()) if skin.any() else 0.0
        res.metrics.update(skin_frac=float(skin.mean()), skin_rule_frac=rule_frac)
        if skin.mean() < 0.10 or rule_frac < 0.5:
            res.issues.append("no_wrist")
            return res

        work = bgr
        if cfg.white_balance:
            exclude = cv2.dilate(skin.astype(np.uint8), np.ones((15, 15), np.uint8)).astype(bool)
            res.wb = estimate_gray_world_gains(bgr, exclude, clip=cfg.wb_clip)
            work = apply_white_balance(bgr, res.wb.gains_bgr, cfg.wb_strength)
            self._wb_warnings(res)
        else:
            res.wb = WhiteBalanceInfo(source="disabled")

        # Sama dengan predict_image() di notebook: load_image(max 2048) -> crop_roi -> thumbnail(CACHE_MAX)
        img = Image.fromarray(cv2.cvtColor(work, cv2.COLOR_BGR2RGB))
        img.thumbnail((2048, 2048), Image.BICUBIC)
        roi = unb.crop_roi(img).copy()
        roi.thumbnail((unb.CACHE_MAX, unb.CACHE_MAX), Image.BICUBIC)
        roi_rgb = np.asarray(roi)

        b, s = _exposure_and_sharpness(cv2.cvtColor(roi_rgb, cv2.COLOR_RGB2BGR))
        res.metrics.update(brightness=b, sharpness=s, roi_area_frac=roi.width * roi.height / (img.width * img.height))
        if b < cfg.min_brightness:
            res.issues.append("too_dark")
        elif b > cfg.max_brightness:
            res.issues.append("overexposed")
        if s < cfg.min_sharpness:
            res.issues.append("blurry")                # fitur urat butuh detail tajam
        res.image_rgb = roi_rgb
        res.ok = not res.issues
        return res

    def process(self, image: bytes | str | np.ndarray, kind: str = "face") -> PreprocessResult:
        bgr = image if isinstance(image, np.ndarray) else decode_image(image)
        if kind == "face":
            return self.process_face(bgr)
        if kind == "wrist":
            return self.process_wrist(bgr)
        raise ValueError(f"kind harus 'face' atau 'wrist', bukan {kind!r}")

    @staticmethod
    def _wb_warnings(res: PreprocessResult) -> None:
        if res.wb.clipped:
            res.warnings.append("strong_color_cast")
        if res.wb.source == "full_frame":
            res.warnings.append("wb_fallback")


# =====================================================================================================
if __name__ == "__main__":
    import argparse
    import json

    ap = argparse.ArgumentParser(description="Uji preprocessing pada satu gambar.")
    ap.add_argument("image")
    ap.add_argument("--kind", choices=["face", "wrist"], default="face")
    ap.add_argument("--out", help="simpan crop hasil preprocessing (PNG)")
    ap.add_argument("--no-wb", action="store_true", help="matikan Gray-World white balance")
    a = ap.parse_args()

    pre = Preprocessor(PreprocessConfig(white_balance=not a.no_wb))
    r = pre.process(Path(a.image).read_bytes(), a.kind)
    print(json.dumps(r.meta(), indent=2, ensure_ascii=False))
    if a.out and r.image_rgb is not None:
        Image.fromarray(r.image_rgb).save(a.out)
        print("crop disimpan:", a.out)
