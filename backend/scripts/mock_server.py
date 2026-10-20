#!/usr/bin/env python3
"""
Server DEMO untuk pengembangan frontend sebelum bobot model asli tersedia.

Memakai pipeline ASLI (preprocessing, deteksi wajah, Gray-World WB, rules engine, palet) tetapi model undertone &
season diganti model kecil berbobot ACAK (tests/tiny_models.py). Bentuk respons identik dengan server produksi,
namun musim/undertone yang keluar TIDAK bermakna.

    python scripts/mock_server.py            # http://localhost:8000
"""
import os
import sys
import tempfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("GLOWMATCH_LOAD_MODELS", "0")

import uvicorn  # noqa: E402

from app.main import create_app  # noqa: E402
from app.pipeline import AnalysisService, load_labels  # noqa: E402
from app.settings import settings  # noqa: E402
from ml.preprocess import PreprocessConfig, Preprocessor  # noqa: E402
from tests import tiny_models as tm  # noqa: E402


def build_service() -> AnalysisService:
    tmp = Path(tempfile.mkdtemp(prefix="glowmatch-mock-"))
    undertone = tm.load_undertone(tm.build_undertone_dir(tmp / "undertone"))
    season = tm.load_season(tm.build_season_dir(tmp / "season", tm.build_season_bundle()))
    pre = Preprocessor(PreprocessConfig(white_balance=settings.white_balance, wb_strength=settings.wb_strength))
    return AnalysisService(pre, load_labels(settings), undertone, season, load_errors={"mode": "MOCK: prediksi acak"})


if __name__ == "__main__":
    print("PERINGATAN: server MOCK — model berbobot acak, hasil analisis tidak bermakna.")
    uvicorn.run(create_app(service=build_service()), host="127.0.0.1", port=int(os.environ.get("PORT", 8000)))
