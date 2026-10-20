import base64
import io
import json

import cv2
import numpy as np
import pytest
from PIL import Image

from ml.preprocess import (
    FaceBox, ImageDecodeError, PreprocessConfig, Preprocessor, _SRGB_TO_LINEAR, _linear_to_srgb_u8,
    apply_white_balance, decode_image, estimate_gray_world_gains, gray_world_white_balance,
)

SKIN_SRGB_BGR = np.array([120, 160, 215], np.uint8)     # kulit hangat (B, G, R)
CAST_LIN_BGR = np.array([0.70, 1.0, 1.35])              # lampu kuning/oranye di ruang linear


def cast(bgr: np.ndarray, gains=CAST_LIN_BGR) -> np.ndarray:
    lut = np.stack([_linear_to_srgb_u8(_SRGB_TO_LINEAR * g) for g in gains], axis=-1)
    return cv2.LUT(bgr, lut.reshape(256, 1, 3))


def lin_mean(bgr, mask=None):
    px = bgr[mask] if mask is not None else bgr.reshape(-1, 3)
    return _SRGB_TO_LINEAR[px].mean(axis=0)


def scene_with_skin(h=240, w=320):
    """Latar abu-abu bertingkat (netral) + elips 'kulit' di tengah."""
    img = np.zeros((h, w, 3), np.uint8)
    for i, v in enumerate(np.linspace(60, 200, 8).astype(np.uint8)):
        img[:, i * w // 8:(i + 1) * w // 8] = v
    skin = np.zeros((h, w), np.uint8)
    cv2.ellipse(skin, (w // 2, h // 2), (60, 80), 0, 0, 360, 1, -1)
    img[skin.astype(bool)] = SKIN_SRGB_BGR
    return img, skin.astype(bool)


# ------------------------------------------------------------------------------------- white balance
def test_lut_roundtrip_is_identity():
    assert np.array_equal(_linear_to_srgb_u8(_SRGB_TO_LINEAR), np.arange(256, dtype=np.uint8))


def test_identity_gains_returns_input():
    img, _ = scene_with_skin()
    assert np.array_equal(apply_white_balance(img, (1.0, 1.0, 1.0)), img)


def test_gray_world_removes_color_cast():
    img, _ = scene_with_skin()
    gray_only = img.copy()
    gray_only[:] = img[:, :1]                       # tanpa kulit: murni latar netral
    out, info = gray_world_white_balance(cast(gray_only))
    m = lin_mean(out)
    assert info.source == "full_frame"
    assert np.ptp(m) / m.mean() < 0.03, m           # B≈G≈R setelah koreksi


def test_skin_undertone_preserved_when_face_excluded():
    img, skin = scene_with_skin()
    lit = cast(img)
    # Benar: gain dari latar, diterapkan ke kulit -> kulit kembali ke warna aslinya (tetap hangat).
    good, info = gray_world_white_balance(lit, exclude_mask=skin)
    assert info.source == "background"
    orig, fixed = lin_mean(img, skin), lin_mean(good, skin)
    assert np.allclose(fixed, orig, rtol=0.06), (fixed, orig)
    # Salah (naif): Gray-World pada crop yang isinya kulit saja -> undertone ternetralkan.
    h, w = skin.shape
    crop = lit[h // 2 - 40:h // 2 + 40, w // 2 - 30:w // 2 + 30]
    naive, _ = gray_world_white_balance(crop, clip=(0.1, 10))
    r_over_b = lambda m: m[2] / m[0]
    assert r_over_b(lin_mean(naive)) < 0.6 * r_over_b(orig)


def test_colorful_background_object_does_not_dominate():
    img, skin = scene_with_skin()
    img[:, :100] = (30, 90, 170)                    # baju/dinding oranye besar di latar (tidak jenuh)
    out, info = gray_world_white_balance(cast(img), exclude_mask=skin)
    gray_cols = out[:, 140:150][~skin[:, 140:150]]
    m = lin_mean(gray_cols[None])
    assert np.ptp(m) / m.mean() < 0.05, (m, info)   # latar abu-abu kembali netral meski ada objek oranye
    assert info.neutral_fraction < 0.8


def test_gains_are_clipped_on_saturated_scene():
    red = np.zeros((100, 100, 3), np.uint8)
    red[:] = (20, 30, 200)
    info = estimate_gray_world_gains(red, clip=(0.67, 1.5))
    assert info.clipped and all(0.67 <= g <= 1.5 for g in info.gains_bgr)


def test_falls_back_to_full_frame_when_background_too_small():
    img, _ = scene_with_skin()
    everything = np.ones(img.shape[:2], bool)
    assert estimate_gray_world_gains(img, everything).source == "full_frame"


# ------------------------------------------------------------------------------------------- decode
def _png_bytes(rgb):
    buf = io.BytesIO()
    Image.fromarray(rgb).save(buf, format="PNG")
    return buf.getvalue()


def test_decode_bytes_base64_and_data_url():
    rgb = np.random.default_rng(0).integers(0, 255, (40, 60, 3), dtype=np.uint8)
    raw = _png_bytes(rgb)
    b64 = base64.b64encode(raw).decode()
    for payload in (raw, b64, "data:image/png;base64," + b64):
        bgr = decode_image(payload)
        assert np.array_equal(bgr[..., ::-1], rgb)


def test_decode_limits_size_and_rejects_garbage():
    big = np.zeros((2000, 3000, 3), np.uint8)
    assert max(decode_image(_png_bytes(big), max_side=1280).shape[:2]) == 1280
    with pytest.raises(ImageDecodeError):
        decode_image(b"bukan gambar")
    with pytest.raises(ImageDecodeError):
        decode_image("%%%")


# ------------------------------------------------------------------------------------------- wajah
class FakeDetector:
    def __init__(self, faces):
        self.faces = faces

    def detect(self, bgr):
        return list(self.faces)


def face_frame():
    img, skin = scene_with_skin(480, 640)
    return cast(img), skin


def test_face_pipeline_crop_box_and_meta():
    frame, _ = face_frame()
    box = FaceBox(250, 160, 140, 160, eyes=((290, 220), (350, 226)))
    r = Preprocessor(detector=FakeDetector([box])).process_face(frame)
    assert r.ok, r.meta()
    x0, y0, x1, y1 = r.crop_box
    assert 0 <= x0 < box.x and x1 > box.x + box.w and y0 < box.y and y1 > box.y + box.h
    assert r.image_rgb.shape == (y1 - y0, x1 - x0, 3)
    assert r.wb.source == "background"
    assert abs(r.metrics["roll_deg"] - np.degrees(np.arctan2(6, 60))) < 1e-6
    json.dumps(r.meta())                                    # harus JSON-serializable


def test_face_pipeline_issues():
    frame, _ = face_frame()
    assert Preprocessor(detector=FakeDetector([])).process_face(frame).issues == ["no_face"]
    tiny = Preprocessor(detector=FakeDetector([FaceBox(300, 200, 30, 36)])).process_face(frame)
    assert "face_too_small" in tiny.issues and not tiny.ok
    dark = (frame * 0.15).astype(np.uint8)
    r = Preprocessor(detector=FakeDetector([FaceBox(250, 160, 140, 160)])).process_face(dark)
    assert "too_dark" in r.issues


def test_wb_can_be_disabled():
    frame, _ = face_frame()
    r = Preprocessor(PreprocessConfig(white_balance=False),
                     detector=FakeDetector([FaceBox(250, 160, 140, 160)])).process_face(frame)
    assert r.wb.source == "disabled"
    assert np.array_equal(r.image_rgb, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)[slice(*r.crop_box[1::2]),
                                                                                 slice(*r.crop_box[::2])])


def test_haar_detects_real_face():
    skimage_data = pytest.importorskip("skimage.data")
    bgr = cv2.cvtColor(skimage_data.astronaut(), cv2.COLOR_RGB2BGR)
    pre = Preprocessor(PreprocessConfig(), detector=__import__("ml.preprocess", fromlist=["x"]).FaceDetector("haar"))
    r = pre.process_face(bgr)
    assert r.box is not None, r.meta()
    x, y, w, h = r.box
    assert 140 < x + w / 2 < 280 and 40 < y + h / 2 < 170      # wajah astronaut ada di kiri-atas tengah


# ------------------------------------------------------------------------------------- pergelangan
def wrist_frame(h=480, w=640):
    rng = np.random.default_rng(1)
    img = np.clip(rng.normal(90, 35, (h, w, 3)), 0, 255).astype(np.uint8)        # latar bertekstur
    img = cv2.GaussianBlur(img, (3, 3), 0)
    arm = np.zeros((h, w), np.uint8)
    cv2.ellipse(arm, (w // 2, h // 2), (150, 210), 0, 0, 360, 1, -1)
    img[arm.astype(bool)] = SKIN_SRGB_BGR
    for dx in (-40, 0, 45):                                                     # "urat" gelap kebiruan
        cv2.line(img, (w // 2 + dx, h // 2 - 150), (w // 2 + dx + 15, h // 2 + 150), (120, 120, 150), 4)
    return cast(img)


def test_wrist_pipeline_crops_to_skin():
    r = Preprocessor(PreprocessConfig(min_sharpness=0), detector=FakeDetector([])).process_wrist(wrist_frame())
    assert r.ok, r.meta()
    h, w = r.image_rgb.shape[:2]
    assert max(h, w) <= 512 and r.metrics["roi_area_frac"] < 0.6
    assert r.wb.source == "background"


def test_wrist_rejects_face_and_empty_frame():
    big_face = FakeDetector([FaceBox(150, 80, 300, 340)])
    assert Preprocessor(detector=big_face).process_wrist(wrist_frame()).issues == ["face_instead_of_wrist"]
    blank = np.full((480, 640, 3), (200, 80, 30), np.uint8)
    assert "no_wrist" in Preprocessor(detector=FakeDetector([])).process_wrist(blank).issues
