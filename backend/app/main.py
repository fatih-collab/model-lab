
"""
GlowMatch API.

Endpoints:
    GET    /api/health
    GET    /api/seasons
    POST   /api/frame/check
    POST   /api/undertone
    POST   /api/analyze

    GET    /api/profile
    POST   /api/profile

    GET    /api/history
    POST   /api/history
    DELETE /api/history/{item_id}

Database:
    Production: Neon PostgreSQL
    Testing: SQLite sementara melalui dependency injection

Catatan:
    Pipeline kamera, preprocessing, face detection,
    dan model klasifikasi tetap menggunakan implementasi lama.
"""

from __future__ import annotations

# Harus diimpor pertama untuk menyiapkan konfigurasi
# Hugging Face sebelum library ML digunakan.
from app.settings import settings  # noqa: I001

import logging
from contextlib import asynccontextmanager
from typing import Literal, Optional

from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
)
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import rules_engine, schemas
from app.db import Database
from app.palettes import palette_for
from app.pipeline import AnalysisService, ModelsNotReady

from ml.preprocess import ImageDecodeError


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


# ============================================================
# SESSION CONFIGURATION
# ============================================================

SESSION_COOKIE_NAME = "glowmatch_session"
SESSION_TTL_DAYS = 30


# ============================================================
# APPLICATION FACTORY
# ============================================================

def create_app(
    service: AnalysisService | None = None,
    database: Database | None = None,
) -> FastAPI:
    """
    Membuat instance aplikasi FastAPI.

    Parameters
    ----------
    service:
        AnalysisService yang sudah tersedia.
        Digunakan untuk dependency injection dan testing.

    database:
        Database instance yang sudah disiapkan.
        Jika None, aplikasi menggunakan Neon PostgreSQL
        melalui settings.database_url.
    """

    # --------------------------------------------------------
    # APPLICATION LIFESPAN
    # --------------------------------------------------------

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """
        Mengelola koneksi database dan model service.

        Production:
            Menggunakan Neon PostgreSQL.

        Testing:
            Menggunakan database yang diinjeksi.
        """

        app_database = (
            database
            if database is not None
            else Database(settings.database_url)
        )

        app.state.database = app_database

        try:
            # Pastikan database tersedia.
            await run_in_threadpool(
                app_database.check_connection
            )

            logger.info(
                "Database connection established."
            )

            # Pertahankan service machine learning yang sudah ada.
            if service is not None:
                app.state.service = service
            else:
                app.state.service = await run_in_threadpool(
                    AnalysisService.from_settings,
                    settings,
                )

            logger.info(
                "GlowMatch application started."
            )

            yield

        finally:
            # Setiap instance aplikasi bertanggung jawab
            # menutup database engine yang digunakannya.
            await run_in_threadpool(
                app_database.dispose
            )

            logger.info(
                "Database connection disposed."
            )

    # --------------------------------------------------------
    # FASTAPI APPLICATION
    # --------------------------------------------------------

    app = FastAPI(
        title="GlowMatch API",
        version="0.2.0",
        description=(
            "12-Season Personal Color Analysis "
            "using wrist undertone detection, "
            "face analysis, and color recommendation."
        ),
        lifespan=lifespan,
    )

    # --------------------------------------------------------
    # CORS CONFIGURATION
    # --------------------------------------------------------

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=[
            "GET",
            "POST",
            "PUT",
            "DELETE",
            "OPTIONS",
        ],
        allow_headers=["*"],
    )

    # --------------------------------------------------------
    # EXCEPTION HANDLERS
    # --------------------------------------------------------

    @app.exception_handler(ImageDecodeError)
    async def bad_image(
        request: Request,
        exc: ImageDecodeError,
    ):
        logger.warning(
            "Image decoding failed: %s",
            exc,
        )

        return JSONResponse(
            status_code=400,
            content={"detail": str(exc)},
        )

    @app.exception_handler(ModelsNotReady)
    async def models_not_ready(
        request: Request,
        exc: ModelsNotReady,
    ):
        logger.error(
            "Machine learning models are not ready: %s",
            exc,
        )

        return JSONResponse(
            status_code=503,
            content={"detail": str(exc)},
        )

    # --------------------------------------------------------
    # DEPENDENCY: ANALYSIS SERVICE
    # --------------------------------------------------------

    def svc(request: Request) -> AnalysisService:
        """
        Mengambil AnalysisService dari application state.
        """

        return request.app.state.service

    # --------------------------------------------------------
    # DEPENDENCY: DATABASE SESSION
    # --------------------------------------------------------

    def current_session_id(
        request: Request,
        response: Response,
    ) -> int:
        """
        Memvalidasi cookie sesi pengguna.

        Jika pengguna belum mempunyai sesi atau sesi
        sudah kedaluwarsa, buat sesi baru.

        Token mentah hanya disimpan dalam cookie browser.
        Database hanya menyimpan hash token.
        """

        database_instance: Database = (
            request.app.state.database
        )

        incoming_token = request.cookies.get(
            SESSION_COOKIE_NAME
        )

        token, session_id = (
            database_instance.resolve_session(
                token=incoming_token,
                ttl_days=SESSION_TTL_DAYS,
            )
        )

        # Cookie hanya diperbarui ketika token baru dibuat.
        if token != incoming_token:
            response.set_cookie(
                key=SESSION_COOKIE_NAME,
                value=token,
                max_age=SESSION_TTL_DAYS * 24 * 60 * 60,
                httponly=True,
                secure=request.url.scheme == "https",
                samesite="lax",
                path="/",
            )

        return session_id

    # --------------------------------------------------------
    # DEPENDENCY: PROFILE COMPLETION
    # --------------------------------------------------------

    def require_complete_profile(
        request: Request,
        session_id: int = Depends(current_session_id),
    ) -> int:
        """
        Memastikan pengguna sudah melengkapi profil
        sebelum memulai proses analisis.
        """

        database_instance: Database = (
            request.app.state.database
        )

        try:
            profile = database_instance.get_profile(
                session_id=session_id,
            )

        except LookupError as exc:
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "PROFILE_INCOMPLETE",
                    "message": (
                        "Lengkapi profil terlebih dahulu "
                        "sebelum memulai analisis."
                    ),
                },
            ) from exc

        if not profile.get("is_complete", False):
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "PROFILE_INCOMPLETE",
                    "message": (
                        "Lengkapi profil terlebih dahulu "
                        "sebelum memulai analisis."
                    ),
                },
            )

        return session_id

    # --------------------------------------------------------
    # HELPER: IMAGE UPLOAD
    # --------------------------------------------------------

    async def read_image(
        uploaded_file: UploadFile | None,
        field: str,
    ) -> bytes | None:
        """
        Membaca gambar dan memastikan batas ukuran file.

        Gambar hanya diproses di memory.
        Tidak disimpan ke PostgreSQL.
        """

        if uploaded_file is None:
            return None

        limit = int(
            settings.max_upload_mb * 1024 * 1024
        )

        data = await uploaded_file.read(limit + 1)

        if len(data) > limit:
            raise HTTPException(
                status_code=413,
                detail=(
                    f"File '{field}' melebihi "
                    f"{settings.max_upload_mb:g} MB."
                ),
            )

        if not data:
            raise HTTPException(
                status_code=400,
                detail=f"File '{field}' kosong.",
            )

        return data

    # ========================================================
    # HEALTH ENDPOINT
    # ========================================================

    @app.get(
        "/api/health",
        response_model=schemas.Health,
    )
    def health(request: Request):
        """
        Memeriksa kesiapan model machine learning.
        """

        status = svc(request).status()

        return {
            "status": (
                "ok"
                if (
                    status["undertone_ready"]
                    and status["season_ready"]
                )
                else "degraded"
            ),
            **status,
        }

    # ========================================================
    # SEASON ENDPOINT
    # ========================================================

    @app.get(
        "/api/seasons",
        response_model=list[schemas.SeasonInfo],
    )
    def seasons(request: Request):
        """
        Mengambil 12 kategori season beserta palet warna.
        """

        labels = svc(request).labels

        return [
            {
                "id": season_id,
                **{
                    key: labels[season_id][key]
                    for key in (
                        "name",
                        "family",
                        "subtype",
                        "undertone",
                    )
                },
                "neighbors": (
                    rules_engine.wheel_neighbors(season_id)
                ),
                "palette": palette_for(season_id),
            }
            for season_id in rules_engine.WHEEL
        ]

    # ========================================================
    # FRAME CHECK ENDPOINT
    # ========================================================

    @app.post(
        "/api/frame/check",
        response_model=schemas.Quality,
    )
    async def frame_check(
        request: Request,
        image: UploadFile = File(...),
        kind: Literal["face", "wrist"] = Form("face"),
        _session_id: int = Depends(require_complete_profile),
    ):
        """
        Preprocessing dan pemeriksaan kualitas frame.
        """

        image_data = await read_image(
            image,
            "image",
        )

        return await run_in_threadpool(
            svc(request).check_frame,
            image_data,
            kind,
        )

    # ========================================================
    # UNDERTONE ANALYSIS ENDPOINT
    # ========================================================

    @app.post(
        "/api/undertone",
        response_model=schemas.UndertoneResponse,
        response_model_exclude_none=True,
    )
    async def undertone(
        request: Request,
        wrist: UploadFile = File(...),
        _session_id: int = Depends(require_complete_profile),
    ):
        """
        Menganalisis undertone melalui foto pergelangan.
        """

        wrist_data = await read_image(
            wrist,
            "wrist",
        )

        return await run_in_threadpool(
            svc(request).analyze_undertone,
            wrist_data,
        )

    # ========================================================
    # PERSONAL COLOR ANALYSIS ENDPOINT
    # ========================================================

    @app.post(
        "/api/analyze",
        response_model=schemas.AnalyzeResponse,
        response_model_exclude_none=True,
    )
    async def analyze(
        request: Request,
        face: UploadFile = File(...),
        wrist: Optional[UploadFile] = File(None),
        undertone: Optional[
            Literal["warm", "cool", "neutral"]
        ] = Form(None),
        debug: bool = Form(False),
        _session_id: int = Depends(require_complete_profile),
    ):
        """
        Melakukan analisis personal color.

        Pipeline yang dipakai tetap:
            - Face preprocessing
            - Face detection
            - Undertone analysis
            - Season classification
            - Rules engine
            - Color recommendation
        """

        face_data = await read_image(
            face,
            "face",
        )

        wrist_data = await read_image(
            wrist,
            "wrist",
        )

        result = await run_in_threadpool(
            svc(request).analyze,
            face_data,
            wrist_data,
            undertone,
            debug,
        )

        return result

    # ========================================================
    # PROFILE ENDPOINTS
    # ========================================================

    @app.get(
        "/api/profile",
        response_model=schemas.Profile,
    )
    def get_profile(
        request: Request,
        session_id: int = Depends(current_session_id),
    ):
        """
        Mengambil profil milik sesi browser aktif.
        """

        database_instance: Database = (
            request.app.state.database
        )

        try:
            return database_instance.get_profile(
                session_id=session_id,
            )

        except LookupError as exc:
            raise HTTPException(
                status_code=404,
                detail=str(exc),
            ) from exc

    @app.post(
        "/api/profile",
        response_model=schemas.Profile,
    )
    def update_profile(
        body: schemas.ProfileUpdate,
        request: Request,
        session_id: int = Depends(current_session_id),
    ):
        """
        Memperbarui profil milik sesi browser aktif.

        Profile ID tidak diterima dari frontend sebagai
        penentu kepemilikan data.
        """

        database_instance: Database = (
            request.app.state.database
        )

        try:
            return database_instance.update_profile(
                session_id=session_id,
                name=body.name,
                gender=body.gender,
                age=body.age,
                notes=body.notes or "",
            )

        except LookupError as exc:
            raise HTTPException(
                status_code=404,
                detail=str(exc),
            ) from exc

    # ========================================================
    # ANALYSIS HISTORY ENDPOINTS
    # ========================================================

    @app.get(
        "/api/history",
        response_model=list[schemas.HistoryItem],
    )
    def get_history(
        request: Request,
        limit: int = Query(
            default=50,
            ge=1,
            le=100,
        ),
        session_id: int = Depends(current_session_id),
    ):
        """
        Mengambil riwayat analisis pengguna.

        Setiap pengguna hanya dapat mengakses riwayat
        yang terhubung dengan sesi miliknya.
        """

        database_instance: Database = (
            request.app.state.database
        )

        return database_instance.get_history(
            session_id=session_id,
            limit=limit,
        )

    @app.post(
        "/api/history",
        response_model=schemas.HistoryItem,
    )
    def create_history(
        body: schemas.HistoryCreate,
        request: Request,
        session_id: int = Depends(current_session_id),
    ):
        """
        Menyimpan hasil analisis ke database.

        profile_id dari client tidak digunakan sebagai
        penentu kepemilikan riwayat.
        """

        database_instance: Database = (
            request.app.state.database
        )

        try:
            return database_instance.add_history(
                session_id=session_id,
                season_id=body.season_id,
                season_name=body.season_name,
                undertone=body.undertone,
                request_id=body.request_id,
                detected_season=body.detected_season,
                undertone_source=(
                    body.undertone_source or "wrist_model"
                ),
                confidence=(
                    1.0
                    if body.confidence is None
                    else body.confidence
                ),
                palette=body.palette,
                notes=body.notes or "",

                # Snapshot hasil klasifikasi lengkap.
                analysis_result=getattr(
                    body,
                    "analysis_result",
                    None,
                ),

                selected_season=getattr(
                    body,
                    "selected_season",
                    None,
                ),

                # Snapshot profil dibuat oleh backend
                # berdasarkan profil pemilik sesi.
                profile_snapshot=None,
            )

        except LookupError as exc:
            raise HTTPException(
                status_code=404,
                detail=str(exc),
            ) from exc

        except PermissionError as exc:
            raise HTTPException(
                status_code=403,
                detail=str(exc),
            ) from exc

    @app.delete(
        "/api/history/{item_id}",
    )
    def delete_history_item(
        item_id: str,
        request: Request,
        session_id: int = Depends(current_session_id),
    ):
        """
        Menghapus riwayat berdasarkan ID atau request_id.

        Penghapusan dibatasi pada pemilik sesi aktif.
        """

        database_instance: Database = (
            request.app.state.database
        )

        success = database_instance.delete_history(
            session_id=session_id,
            history_id=item_id,
        )

        if not success:
            raise HTTPException(
                status_code=404,
                detail="Data riwayat tidak ditemukan.",
            )

        return {
            "status": "ok",
            "deleted_id": item_id,
        }

    # --------------------------------------------------------
    # RETURN APPLICATION
    # --------------------------------------------------------

    return app


# ============================================================
# DEFAULT APPLICATION INSTANCE
# ============================================================

app = create_app()
