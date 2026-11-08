
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


LABELS = json.loads(
    (settings.models_dir / "manifest.json").read_text()
)["modules"]["season"]["labels"]

FACE_BOX = FaceBox(
    250,
    160,
    140,
    160,
    eyes=((290, 220), (350, 222)),
)


def jpeg(bgr) -> bytes:
    """Mengubah frame BGR menjadi JPEG."""

    buf = io.BytesIO()

    Image.fromarray(
        cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    ).save(
        buf,
        format="JPEG",
        quality=95,
    )

    return buf.getvalue()


class RoutingDetector(FakeDetector):
    """
    Wajah hanya terdeteksi pada frame wajah.
    Frame pergelangan menggunakan latar noise.
    """

    def detect(self, bgr):
        noise = np.abs(
            np.diff(
                bgr[..., 1].astype(np.int16),
                axis=1,
            )
        ).mean()

        return [FACE_BOX] if noise < 5 else []


def make_client(
    undertone_model=None,
    season_model=None,
) -> TestClient:
    """
    Membuat TestClient dengan database SQLite sementara.

    Database dibuat terpisah untuk setiap pengujian.
    """

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


@pytest.fixture
def client(undertone_model, season_model):
    """
    Setiap test mendapatkan client, session,
    dan database sementara yang baru.
    """

    with make_client(
        undertone_model,
        season_model,
    ) as c:
        yield c


FACE = jpeg(face_frame()[0])
WRIST = jpeg(wrist_frame())


def complete_profile(client):
    """
    Mengisi profil melalui endpoint API.

    Digunakan oleh pengujian yang memang membutuhkan
    akses ke endpoint analisis.
    """

    response = client.post(
        "/api/profile",
        json={
            "name": "Pengguna Test GlowMatch",
            "gender": "wanita",
            "age": 24,
            "notes": "Testing profile",
        },
    )

    assert response.status_code == 200, response.text

    profile = response.json()

    assert profile["is_complete"] is True

    return profile


def test_health_and_seasons(client):
    h = client.get("/api/health").json()

    assert (
        h["status"] == "ok"
        and h["undertone_ready"]
        and h["season_ready"]
    )

    seasons = client.get("/api/seasons").json()

    assert len(seasons) == 12

    assert all(
        len(s["palette"]["palettes"]["utama"]) == 10
        for s in seasons
    )

    soft_summer = next(
        s for s in seasons
        if s["name"] == "Soft Summer"
    )

    assert "autunno_soft" in soft_summer["neighbors"]


def test_analysis_endpoints_require_complete_profile(client):
    """
    Memastikan seluruh endpoint analisis menolak
    pengguna yang belum melengkapi profil.
    """

    profile_response = client.get("/api/profile")

    assert profile_response.status_code == 200
    assert profile_response.json()["is_complete"] is False

    # Frame check harus ditolak.
    frame_response = client.post(
        "/api/frame/check",
        files={
            "image": ("f.jpg", FACE, "image/jpeg")
        },
        data={"kind": "face"},
    )

    assert frame_response.status_code == 403
    assert (
        frame_response.json()["detail"]["code"]
        == "PROFILE_INCOMPLETE"
    )

    # Undertone harus ditolak.
    undertone_response = client.post(
        "/api/undertone",
        files={
            "wrist": ("w.jpg", WRIST, "image/jpeg")
        },
    )

    assert undertone_response.status_code == 403
    assert (
        undertone_response.json()["detail"]["code"]
        == "PROFILE_INCOMPLETE"
    )

    # Analisis wajah harus ditolak.
    analyze_response = client.post(
        "/api/analyze",
        files={
            "face": ("f.jpg", FACE, "image/jpeg")
        },
    )

    assert analyze_response.status_code == 403
    assert (
        analyze_response.json()["detail"]["code"]
        == "PROFILE_INCOMPLETE"
    )


def test_frame_check(client):
    complete_profile(client)

    response = client.post(
        "/api/frame/check",
        files={
            "image": ("f.jpg", FACE, "image/jpeg")
        },
        data={"kind": "face"},
    )

    assert response.status_code == 200, response.text

    quality = response.json()

    assert quality["ok"]
    assert quality["box"] == [
        250.0,
        160.0,
        140.0,
        160.0,
    ]

    assert quality["white_balance"]["source"] == "background"


def test_undertone_endpoint(client):
    complete_profile(client)

    response = client.post(
        "/api/undertone",
        files={
            "wrist": ("w.jpg", WRIST, "image/jpeg")
        },
    )

    assert response.status_code == 200, response.text

    body = response.json()

    assert body["status"] == "ok"

    assert body["undertone"]["label"] in (
        "cool",
        "neutral",
        "warm",
    )


def test_analyze_with_wrist_applies_gate(client):
    complete_profile(client)

    response = client.post(
        "/api/analyze",
        files={
            "face": ("f.jpg", FACE, "image/jpeg"),
            "wrist": ("w.jpg", WRIST, "image/jpeg"),
        },
    )

    assert response.status_code == 200, response.text

    body = response.json()

    result = body["result"]
    undertone = body["undertone"]["label"]

    if undertone == "neutral":
        assert not result["gate"]["applied"]
    else:
        assert result["gate"]["applied"]
        assert result["season"]["undertone"] == undertone

    assert result["season"]["palette"]["palettes"]["utama"]

    assert len(result["neighbors"]) >= 2

    assert all(
        "palette" in neighbor
        for neighbor in result["neighbors"]
    )

    assert set(body["timings_ms"]) >= {
        "undertone",
        "season",
        "total",
    }


@pytest.mark.parametrize(
    "label,families",
    [
        ("warm", {"Spring", "Autumn"}),
        ("cool", {"Summer", "Winter"}),
    ],
)
def test_analyze_with_client_undertone_label(
    client,
    label,
    families,
):
    complete_profile(client)

    response = client.post(
        "/api/analyze",
        files={
            "face": ("f.jpg", FACE, "image/jpeg")
        },
        data={"undertone": label},
    )

    assert response.status_code == 200, response.text

    body = response.json()

    assert body["result"]["season"]["family"] in families
    assert body["undertone"]["source"] == "client"


def test_analyze_without_undertone_is_neutral(client):
    complete_profile(client)

    response = client.post(
        "/api/analyze",
        files={
            "face": ("f.jpg", FACE, "image/jpeg")
        },
        data={"debug": "true"},
    )

    assert response.status_code == 200, response.text

    body = response.json()

    assert (
        body["result"]["gate"]["undertone_source"]
        == "season_model"
    )

    assert body["debug"]["rgbm_png"]
    assert body["debug"]["face_crop_png"]


def test_analyze_rejects_bad_face_frame(client):
    complete_profile(client)

    dark = jpeg(
        (face_frame()[0] * 0.1).astype(np.uint8)
    )

    response = client.post(
        "/api/analyze",
        files={
            "face": ("f.jpg", dark, "image/jpeg")
        },
    )

    assert response.status_code == 200, response.text

    body = response.json()

    assert body["status"] == "rejected"
    assert body["stage"] == "face"
    assert body["messages"]


def test_bad_inputs(client):
    complete_profile(client)

    # Gambar tidak valid.
    invalid_image = client.post(
        "/api/analyze",
        files={
            "face": ("f.jpg", b"xx", "image/jpeg")
        },
    )

    assert invalid_image.status_code == 400

    # Face wajib tersedia.
    missing_face = client.post(
        "/api/analyze",
        data={"undertone": "warm"},
    )

    assert missing_face.status_code == 422

    # Undertone hanya menerima nilai yang diizinkan.
    invalid_undertone = client.post(
        "/api/analyze",
        files={
            "face": ("f.jpg", FACE, "image/jpeg")
        },
        data={"undertone": "hot"},
    )

    assert invalid_undertone.status_code == 422


def test_503_when_models_missing():
    with make_client() as client:
        # Health tetap dapat diperiksa.
        assert client.get(
            "/api/health"
        ).json()["status"] == "degraded"

        # Profil harus lengkap agar pengujian mencapai
        # pemeriksaan kesiapan model.
        complete_profile(client)

        response = client.post(
            "/api/analyze",
            files={
                "face": ("f.jpg", FACE, "image/jpeg")
            },
        )

        assert response.status_code == 503

        # Frame check tetap berjalan tanpa model ML.
        frame_response = client.post(
            "/api/frame/check",
            files={
                "image": ("f.jpg", FACE, "image/jpeg")
            },
        )

        assert frame_response.status_code == 200


def test_profile_endpoints(client):
    # Profil baru harus belum lengkap.
    response = client.get("/api/profile")

    assert response.status_code == 200

    profile = response.json()

    assert "name" in profile
    assert "gender" in profile
    assert profile["is_complete"] is False

    # Mengisi profil melalui API.
    update_response = client.post(
        "/api/profile",
        json={
            "name": "Alya Maharani",
            "gender": "wanita",
            "age": 24,
            "notes": "Kulit sawo matang",
        },
    )

    assert update_response.status_code == 200

    updated = update_response.json()

    assert updated["name"] == "Alya Maharani"
    assert updated["age"] == 24
    assert updated["is_complete"] is True


def test_history_endpoints(client):
    complete_profile(client)

    data = {
        "season_id": "primavera_warm",
        "season_name": "True Spring",
        "undertone": "warm",
        "request_id": "req_test_123",
        "detected_season": "True Spring",
        "confidence": 0.95,
        "palette": [
            "#FF7F5E",
            "#FFC93C",
            "#2EC4B6",
        ],
        "notes": "Testing history creation",
    }

    # POST history.
    response = client.post(
        "/api/history",
        json=data,
    )

    assert response.status_code == 200, response.text

    item = response.json()

    assert item["season_name"] == "True Spring"
    assert len(item["palette"]) == 3

    # GET history.
    list_response = client.get("/api/history")

    assert list_response.status_code == 200

    history = list_response.json()

    assert len(history) >= 1

    assert any(
        item["request_id"] == "req_test_123"
        for item in history
    )

    # DELETE history.
    delete_response = client.delete(
        "/api/history/req_test_123"
    )

    assert delete_response.status_code == 200
