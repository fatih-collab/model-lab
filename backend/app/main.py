"""
GlowMatch API — Fase 2.

Endpoint:
  GET  /api/health          status model & konfigurasi
  GET  /api/seasons         12 musim + tetangga + palet (untuk halaman palet & swapping)
  POST /api/frame/check     preprocessing saja (cepat, tanpa model): umpan balik live + box wajah untuk cincin palet
  POST /api/undertone       foto pergelangan -> undertone (langkah 2 di frontend)
  POST /api/analyze         foto wajah (+ foto pergelangan ATAU label undertone) -> 12-season + gatekeeper + tetangga

Jalankan:  uvicorn app.main:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

from app.settings import settings  # noqa: I001  (harus pertama: men-set cache Hugging Face)

import logging
from contextlib import asynccontextmanager
from typing import Literal, Optional

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import db, rules_engine, schemas
from app.palettes import palette_for
from app.pipeline import AnalysisService, ModelsNotReady
from ml.preprocess import ImageDecodeError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def create_app(service: AnalysisService | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        db.init_db()
        app.state.service = service or await run_in_threadpool(AnalysisService.from_settings, settings)
        yield

    app = FastAPI(title="GlowMatch API", version="0.2.0", lifespan=lifespan,
                  description="12-Season Personal Color Analysis (undertone pergelangan + season wajah).")
    app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins), allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                       allow_headers=["*"])

    @app.exception_handler(ImageDecodeError)
    async def _bad_image(_: Request, exc: ImageDecodeError):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(ModelsNotReady)
    async def _not_ready(_: Request, exc: ModelsNotReady):
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    def svc(request: Request) -> AnalysisService:
        return request.app.state.service

    async def read_image(f: UploadFile | None, field: str) -> bytes | None:
        if f is None:
            return None
        limit = int(settings.max_upload_mb * 1024 * 1024)
        data = await f.read(limit + 1)
        if len(data) > limit:
            raise HTTPException(413, f"File '{field}' melebihi {settings.max_upload_mb:g} MB.")
        if not data:
            raise HTTPException(400, f"File '{field}' kosong.")
        return data

    @app.get("/api/health", response_model=schemas.Health)
    def health(request: Request):
        st = svc(request).status()
        return {"status": "ok" if st["undertone_ready"] and st["season_ready"] else "degraded", **st}

    @app.get("/api/seasons", response_model=list[schemas.SeasonInfo])
    def seasons(request: Request):
        labels = svc(request).labels
        return [{"id": sid, **{k: labels[sid][k] for k in ("name", "family", "subtype", "undertone")},
                 "neighbors": rules_engine.wheel_neighbors(sid), "palette": palette_for(sid)}
                for sid in rules_engine.WHEEL]

    @app.post("/api/frame/check", response_model=schemas.Quality)
    async def frame_check(request: Request, image: UploadFile = File(...),
                          kind: Literal["face", "wrist"] = Form("face")):
        data = await read_image(image, "image")
        return await run_in_threadpool(svc(request).check_frame, data, kind)

    @app.post("/api/undertone", response_model=schemas.UndertoneResponse, response_model_exclude_none=True)
    async def undertone(request: Request, wrist: UploadFile = File(...)):
        data = await read_image(wrist, "wrist")
        return await run_in_threadpool(svc(request).analyze_undertone, data)

    @app.post("/api/analyze", response_model=schemas.AnalyzeResponse, response_model_exclude_none=True)
    async def analyze(request: Request, face: UploadFile = File(...), wrist: Optional[UploadFile] = File(None),
                      undertone: Optional[Literal["warm", "cool", "neutral"]] = Form(None),
                      debug: bool = Form(False)):
        face_data = await read_image(face, "face")
        wrist_data = await read_image(wrist, "wrist")
        return await run_in_threadpool(svc(request).analyze, face_data, wrist_data, undertone, debug)

    # Endpoint Profil Pengguna
    @app.get("/api/profile", response_model=schemas.Profile)
    def get_profile():
        return db.get_profile()

    @app.post("/api/profile", response_model=schemas.Profile)
    def update_profile(body: schemas.ProfileUpdate):
        return db.update_profile(name=body.name, gender=body.gender, age=body.age, notes=body.notes or "")

    # Endpoint Riwayat Analisis
    @app.get("/api/history", response_model=list[schemas.HistoryItem])
    def get_history(limit: int = 50):
        return db.get_history(limit=limit)

    @app.post("/api/history", response_model=schemas.HistoryItem)
    def create_history(body: schemas.HistoryCreate):
        return db.add_history(
            season_id=body.season_id,
            season_name=body.season_name,
            undertone=body.undertone,
            request_id=body.request_id,
            detected_season=body.detected_season,
            undertone_source=body.undertone_source or "wrist_model",
            confidence=body.confidence or 1.0,
            palette=body.palette,
            notes=body.notes or "",
            profile_id=body.profile_id
        )

    @app.delete("/api/history/{item_id}")
    def delete_history_item(item_id: str):
        success = db.delete_history(item_id)
        if not success:
            raise HTTPException(404, "Data riwayat tidak ditemukan.")
        return {"status": "ok", "deleted_id": item_id}

    return app


app = create_app()
