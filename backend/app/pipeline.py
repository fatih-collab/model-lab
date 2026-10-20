"""
Orkestrasi analisis: preprocessing -> inferensi Undertone (pergelangan) -> inferensi Season (wajah) -> rules engine.
Model dimuat sekali saat startup; inferensi diserialisasi dengan lock (model CPU berat, paralel hanya memperlambat).
"""
from __future__ import annotations

import base64
import io
import json
import logging
import threading
import time
import uuid
from dataclasses import asdict
from typing import Protocol

import numpy as np
from PIL import Image

from app import rules_engine
from app.palettes import palette_for
from app.settings import Settings
from ml.preprocess import PreprocessConfig, Preprocessor, PreprocessResult

log = logging.getLogger("glowmatch")


class ModelsNotReady(RuntimeError):
    pass


class UndertonePredictor(Protocol):
    def predict(self, roi_rgb: np.ndarray): ...


class SeasonPredictor(Protocol):
    class_names: list[str]

    def predict(self, face_rgb: np.ndarray): ...


def load_labels(settings: Settings) -> dict[str, dict]:
    manifest = json.loads((settings.models_dir / "manifest.json").read_text(encoding="utf-8"))
    return manifest["modules"]["season"]["labels"]


def _png_b64(rgb: np.ndarray) -> str:
    buf = io.BytesIO()
    Image.fromarray(rgb).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _rejected(stage: str, quality: dict) -> dict:
    return {"status": "rejected", "stage": stage, "quality": quality,
            "messages": quality[stage]["messages"] if quality.get(stage) else []}


class AnalysisService:
    def __init__(self, preprocessor: Preprocessor, labels: dict[str, dict],
                 undertone_model: UndertonePredictor | None = None, season_model: SeasonPredictor | None = None,
                 load_errors: dict[str, str] | None = None, device: str = "cpu"):
        self.pre, self.labels = preprocessor, labels
        self.undertone_model, self.season_model = undertone_model, season_model
        self.load_errors, self.device = load_errors or {}, device
        self._lock = threading.Lock()

    @classmethod
    def from_settings(cls, s: Settings) -> "AnalysisService":
        pre = Preprocessor(PreprocessConfig(white_balance=s.white_balance, wb_strength=s.wb_strength))
        labels, errors, models, device = load_labels(s), {}, {}, "cpu"
        if s.load_models:
            import torch

            from ml.season_model import SeasonModel
            from ml.undertone_model import UndertoneModel

            if s.torch_threads > 0:
                torch.set_num_threads(s.torch_threads)
            device = ("cuda" if torch.cuda.is_available() else "cpu") if s.device == "auto" else s.device
            for name, loader in (("undertone", UndertoneModel), ("season", SeasonModel)):
                t0 = time.perf_counter()
                try:
                    models[name] = loader.load(s.models_dir / name, device=device, max_folds=s.max_folds)
                    log.info("model %s dimuat (%.1fs, %s)", name, time.perf_counter() - t0, device)
                except Exception as e:                       # API tetap hidup; /api/health melaporkan errornya
                    errors[name] = f"{type(e).__name__}: {e}"
                    log.exception("gagal memuat model %s", name)
        else:
            errors = {"undertone": "GLOWMATCH_LOAD_MODELS=0", "season": "GLOWMATCH_LOAD_MODELS=0"}
        return cls(pre, labels, models.get("undertone"), models.get("season"), errors, device)

    # ------------------------------------------------------------------------------------------------
    def status(self) -> dict:
        return {"undertone_ready": self.undertone_model is not None, "season_ready": self.season_model is not None,
                "device": self.device, "detector": self.pre.detector.backend,
                "white_balance": self.pre.cfg.white_balance, "load_errors": self.load_errors}

    def check_frame(self, data: bytes, kind: str) -> dict:
        """Preprocessing saja (tanpa model): untuk umpan balik live & posisi cincin palet."""
        t0 = time.perf_counter()
        meta = self.pre.process(data, kind).meta()
        meta["ms"] = round((time.perf_counter() - t0) * 1000, 1)
        return meta

    def _undertone(self, wrist: PreprocessResult) -> tuple[dict, float]:
        if self.undertone_model is None:
            raise ModelsNotReady(f"Model undertone belum siap: {self.load_errors.get('undertone', '-')}")
        with self._lock:
            r = self.undertone_model.predict(wrist.image_rgb)
        return {"label": r.label, "probs": r.probs, "confidence": round(r.confidence, 4),
                "components": r.components, "source": "wrist_model"}, r.ms

    def analyze_undertone(self, wrist_data: bytes) -> dict:
        t0 = time.perf_counter()
        wrist = self.pre.process(wrist_data, "wrist")
        quality = {"wrist": wrist.meta()}
        if not wrist.ok:
            return _rejected("wrist", quality)
        undertone, ms = self._undertone(wrist)
        return {"status": "ok", "request_id": uuid.uuid4().hex[:12], "undertone": undertone, "quality": quality,
                "timings_ms": {"undertone": round(ms, 1), "total": round((time.perf_counter() - t0) * 1000, 1)}}

    def analyze(self, face_data: bytes, wrist_data: bytes | None = None, undertone_label: str | None = None,
                debug: bool = False) -> dict:
        t0 = time.perf_counter()
        if self.season_model is None:
            raise ModelsNotReady(f"Model season belum siap: {self.load_errors.get('season', '-')}")
        face = self.pre.process(face_data, "face")
        quality = {"face": face.meta(), "wrist": None}
        timings = {"preprocess_face": round((time.perf_counter() - t0) * 1000, 1)}
        if not face.ok:
            return _rejected("face", quality)

        # 1) Undertone (pergelangan) lebih dulu — hasilnya mengunci keluarga musim.
        undertone = None
        if wrist_data is not None:
            wrist = self.pre.process(wrist_data, "wrist")
            quality["wrist"] = wrist.meta()
            if not wrist.ok:
                return _rejected("wrist", quality)
            undertone, timings["undertone"] = self._undertone(wrist)
        elif undertone_label is not None:
            undertone = {"label": undertone_label, "probs": None, "confidence": None, "components": {},
                         "source": "client"}           # hasil /api/undertone sebelumnya

        # 2) Season (wajah)
        with self._lock:
            season = self.season_model.predict(face.image_rgb)
        timings["season"] = round(season.ms, 1)

        # 3) Rules engine
        probs = {c: float(p) for c, p in zip(season.class_names, season.probs)}
        d = rules_engine.decide(probs, self.labels, undertone["label"] if undertone else None)
        with_palette = lambda o: {**asdict(o), "palette": palette_for(o.id)}
        result = {
            "season": {**with_palette(d.final), "confidence_status": season.status},
            "neighbors": [with_palette(n) for n in d.neighbors],
            "gate": {"undertone": d.undertone, "undertone_source": d.undertone_source, "applied": d.gate_applied,
                     "rule": d.rule, "allowed_families": d.allowed_families, "model_choice": d.model_choice,
                     "overridden": d.overridden, "conflict": d.conflict, "season_p_warm": d.season_p_warm,
                     "lean": d.lean},
            "ranking": [asdict(o) for o in d.ranking],
            "candidates": season.candidates,
        }
        timings["total"] = round((time.perf_counter() - t0) * 1000, 1)
        out = {"status": "ok", "request_id": uuid.uuid4().hex[:12], "result": result, "undertone": undertone,
               "quality": quality, "timings_ms": timings}
        if debug:
            out["debug"] = {"face_crop_png": _png_b64(face.image_rgb), "season_components": season.components,
                            "rgbm_png": _png_b64(season.rgbm) if season.rgbm is not None else None}
        log.info("analyze %s -> %s (undertone=%s, overridden=%s, %.0f ms)", out["request_id"], d.final.id,
                 d.undertone, d.overridden, timings["total"])
        return out
