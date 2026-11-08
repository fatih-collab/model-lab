"""End-to-end API: preprocessing nyata + model kecil berbobot acak + rules engine nyata."""
import io
import json

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from app.db import Database

from app.main import create_app
from app.pipeline import AnalysisService
from app.settings import settings
from ml.preprocess import FaceBox, PreprocessConfig, Preprocessor
from tests.test_preprocess import FakeDetector, face_frame, wrist_frame

LABELS = json.loads((settings.models_dir / "manifest.json").read_text())["modules"]["season"]["labels"]
FACE_BOX = FaceBox(250, 160, 140, 160, eyes=((290, 220), (350, 222)))


def jpeg(bgr) -> bytes:
    buf = io.BytesIO()
    Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)).save(buf, format="JPEG", quality=95)
    return buf.getvalue()


class RoutingDetector(FakeDetector):
    """Wajah hanya 'terdeteksi' pada frame wajah (frame pergelangan berlatar noise)."""

    def detect(self, bgr):
        noise = np.abs(np.diff(bgr[..., 1].astype(np.int16), axis=1)).mean()
        return [FACE_BOX] if noise < 5 else []



def make_client(undertone_model=None, season_model=None) -> TestClient:
    pre = Preprocessor(
        PreprocessConfig(min_sharpness=0),
        detector=RoutingDetector([]),
    )

    pre.detector.backend = "fake"

    svc = AnalysisService(
        pre,
        LABELS,
        undertone_model,
        season_model,
        load_errors={},
    )

    test_database = Database(
        "sqlite+pysqlite:///:memory:",
        create_schema=True,
    )

    return TestClient(
        create_app(
            service=svc,
            database=test_database,
        )
    )



@pytest.fixture(scope="module")
def client(undertone_model, season_model):
    with make_client(undertone_model, season_model) as c:
        yield c


FACE = jpeg(face_frame()[0])
WRIST = jpeg(wrist_frame())


def test_health_and_seasons(client):
    h = client.get("/api/health").json()
    assert h["status"] == "ok" and h["undertone_ready"] and h["season_ready"]
    seasons = client.get("/api/seasons").json()
    assert len(seasons) == 12 and all(len(s["palette"]["palettes"]["utama"]) == 10 for s in seasons)
    soft_summer = next(s for s in seasons if s["name"] == "Soft Summer")
    assert "autunno_soft" in soft_summer["neighbors"]


def test_frame_check(client):
    r = client.post("/api/frame/check", files={"image": ("f.jpg", FACE, "image/jpeg")}, data={"kind": "face"})
    assert r.status_code == 200, r.text
    q = r.json()
    assert q["ok"] and q["box"] == [250.0, 160.0, 140.0, 160.0] and q["white_balance"]["source"] == "background"


def test_undertone_endpoint(client):
    r = client.post("/api/undertone", files={"wrist": ("w.jpg", WRIST, "image/jpeg")})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "ok" and body["undertone"]["label"] in ("cool", "neutral", "warm")


def test_analyze_with_wrist_applies_gate(client):
    r = client.post("/api/analyze", files={"face": ("f.jpg", FACE, "image/jpeg"), "wrist": ("w.jpg", WRIST, "image/jpeg")})
    assert r.status_code == 200, r.text
    body = r.json()
    res, ut = body["result"], body["undertone"]["label"]
    if ut == "neutral":
        assert not res["gate"]["applied"]
    else:
        assert res["gate"]["applied"] and res["season"]["undertone"] == ut
    assert res["season"]["palette"]["palettes"]["utama"]
    assert len(res["neighbors"]) >= 2 and all("palette" in n for n in res["neighbors"])
    assert set(body["timings_ms"]) >= {"undertone", "season", "total"}


@pytest.mark.parametrize("label,families", [("warm", {"Spring", "Autumn"}), ("cool", {"Summer", "Winter"})])
def test_analyze_with_client_undertone_label(client, label, families):
    r = client.post("/api/analyze", files={"face": ("f.jpg", FACE, "image/jpeg")}, data={"undertone": label})
    body = r.json()
    assert body["result"]["season"]["family"] in families
    assert body["undertone"]["source"] == "client"


def test_analyze_without_undertone_is_neutral(client):
    body = client.post("/api/analyze", files={"face": ("f.jpg", FACE, "image/jpeg")}, data={"debug": "true"}).json()
    assert body["result"]["gate"]["undertone_source"] == "season_model"
    assert body["debug"]["rgbm_png"] and body["debug"]["face_crop_png"]


def test_analyze_rejects_bad_face_frame(client):
    dark = jpeg((face_frame()[0] * 0.1).astype(np.uint8))
    body = client.post("/api/analyze", files={"face": ("f.jpg", dark, "image/jpeg")}).json()
    assert body["status"] == "rejected" and body["stage"] == "face" and body["messages"]


def test_bad_inputs(client):
    assert client.post("/api/analyze", files={"face": ("f.jpg", b"xx", "image/jpeg")}).status_code == 400
    assert client.post("/api/analyze", data={"undertone": "warm"}).status_code == 422
    r = client.post("/api/analyze", files={"face": ("f.jpg", FACE, "image/jpeg")}, data={"undertone": "hot"})
    assert r.status_code == 422


def test_503_when_models_missing():
    with make_client() as c:
        assert c.get("/api/health").json()["status"] == "degraded"
        r = c.post("/api/analyze", files={"face": ("f.jpg", FACE, "image/jpeg")})
        assert r.status_code == 503
        # pengecekan frame tetap jalan tanpa model
        assert c.post("/api/frame/check", files={"image": ("f.jpg", FACE, "image/jpeg")}).status_code == 200


def test_profile_endpoints(client):
    # GET profile
    r = client.get("/api/profile")
    assert r.status_code == 200
    prof = r.json()
    assert "name" in prof and "gender" in prof

    # POST profile (update)
    r2 = client.post("/api/profile", json={"name": "Alya Maharani", "gender": "wanita", "age": 24, "notes": "Kulit sawo matang"})
    assert r2.status_code == 200
    updated = r2.json()
    assert updated["name"] == "Alya Maharani"
    assert updated["age"] == 24


def test_history_endpoints(client):
    # POST history
    data = {
        "season_id": "primavera_warm",
        "season_name": "True Spring",
        "undertone": "warm",
        "request_id": "req_test_123",
        "detected_season": "True Spring",
        "confidence": 0.95,
        "palette": ["#FF7F5E", "#FFC93C", "#2EC4B6"],
        "notes": "Testing history creation"
    }
    r = client.post("/api/history", json=data)
    assert r.status_code == 200
    item = r.json()
    assert item["season_name"] == "True Spring"
    assert len(item["palette"]) == 3

    # GET history
    r_list = client.get("/api/history")
    assert r_list.status_code == 200
    hist = r_list.json()
    assert len(hist) >= 1
    assert any(h["request_id"] == "req_test_123" for h in hist)

    # DELETE history
    r_del = client.delete(f"/api/history/req_test_123")
    assert r_del.status_code == 200

