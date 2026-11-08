"""
Database SQLite untuk GlowMatch — profil pengguna dan riwayat analisis.
File database disimpan di backend/glowmatch.db (atau sesuai GLOWMATCH_DB_PATH).
"""
from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base
import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
import hashlib
import secrets
import uuid

from datetime import datetime, timedelta, timezone

from sqlalchemy import (
    create_engine,
    delete,
    or_,
    select,
    text,
)

from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import (
    AnalysisHistory,
    Base,
    Profile,
    UserSession,
)

BACKEND_DIR = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.environ.get("GLOWMATCH_DB_PATH", str(BACKEND_DIR / "glowmatch.db")))


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Inisialisasi tabel profil dan riwayat analisis jika belum ada."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Tabel Profil Pengguna
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL DEFAULT 'Pengguna GlowMatch',
                gender TEXT NOT NULL DEFAULT 'wanita',
                age INTEGER DEFAULT 22,
                notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabel Riwayat Analisis
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT UNIQUE,
                profile_id INTEGER,
                season_id TEXT NOT NULL,
                season_name TEXT NOT NULL,
                detected_season TEXT,
                undertone TEXT NOT NULL,
                undertone_source TEXT DEFAULT 'wrist_model',
                confidence REAL DEFAULT 1.0,
                palette_json TEXT NOT NULL DEFAULT '[]',
                notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (profile_id) REFERENCES profiles(id)
            )
        """)
        
        # Buat profil default jika tabel masih kosong
        cursor.execute("SELECT COUNT(*) FROM profiles")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO profiles (name, gender, age, notes) VALUES (?, ?, ?, ?)",
                ("Pengguna GlowMatch", "wanita", 22, "Profil utama")
            )
        conn.commit()


def get_profile() -> dict[str, Any]:
    """Mengambil profil aktif (profil pertama/terbaru)."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, gender, age, notes, created_at, updated_at FROM profiles ORDER BY id ASC LIMIT 1")
        row = cursor.fetchone()
        if not row:
            cursor.execute(
                "INSERT INTO profiles (name, gender, age, notes) VALUES (?, ?, ?, ?)",
                ("Pengguna GlowMatch", "wanita", 22, "Profil utama")
            )
            conn.commit()
            return {"id": 1, "name": "Pengguna GlowMatch", "gender": "wanita", "age": 22, "notes": "Profil utama"}
        return dict(row)


def update_profile(name: str, gender: str = "wanita", age: Optional[int] = None, notes: str = "") -> dict[str, Any]:
    """Menyimpan atau memperbarui profil pengguna."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM profiles ORDER BY id ASC LIMIT 1")
        row = cursor.fetchone()
        now = datetime.now().isoformat()
        if row:
            profile_id = row[0]
            cursor.execute(
                """
                UPDATE profiles 
                SET name = ?, gender = ?, age = ?, notes = ?, updated_at = ?
                WHERE id = ?
                """,
                (name, gender, age, notes, now, profile_id)
            )
        else:
            cursor.execute(
                """
                INSERT INTO profiles (name, gender, age, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (name, gender, age, notes, now, now)
            )
            profile_id = cursor.lastrowid
        conn.commit()
        
        cursor.execute("SELECT id, name, gender, age, notes, created_at, updated_at FROM profiles WHERE id = ?", (profile_id,))
        return dict(cursor.fetchone())


def get_history(limit: int = 50) -> list[dict[str, Any]]:
    """Mengambil daftar riwayat analisis."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                h.id, h.request_id, h.profile_id, h.season_id, h.season_name, 
                h.detected_season, h.undertone, h.undertone_source, h.confidence,
                h.palette_json, h.notes, h.created_at,
                p.name as user_name, p.gender as user_gender, p.age as user_age
            FROM analysis_history h
            LEFT JOIN profiles p ON h.profile_id = p.id
            ORDER BY h.id DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            try:
                d["palette"] = json.loads(d.get("palette_json") or "[]")
            except Exception:
                d["palette"] = []
            result.append(d)
        return result


def add_history(
    season_id: str,
    season_name: str,
    undertone: str,
    request_id: Optional[str] = None,
    detected_season: Optional[str] = None,
    undertone_source: str = "wrist_model",
    confidence: float = 1.0,
    palette: Optional[list[str]] = None,
    notes: str = "",
    profile_id: Optional[int] = None
) -> dict[str, Any]:
    """Menyimpan entri riwayat analisis baru."""
    init_db()
    if not request_id:
        request_id = f"gm_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    if palette is None:
        palette = []
    
    with get_connection() as conn:
        cursor = conn.cursor()
        if not profile_id:
            cursor.execute("SELECT id FROM profiles ORDER BY id ASC LIMIT 1")
            prof_row = cursor.fetchone()
            profile_id = prof_row[0] if prof_row else 1
            
        palette_json = json.dumps(palette)
        now = datetime.now().isoformat()
        
        # Cek apakah request_id sudah ada
        cursor.execute("SELECT id FROM analysis_history WHERE request_id = ?", (request_id,))
        existing = cursor.fetchone()
        if existing:
            cursor.execute("""
                UPDATE analysis_history
                SET season_id = ?, season_name = ?, detected_season = ?, undertone = ?,
                    undertone_source = ?, confidence = ?, palette_json = ?, notes = ?
                WHERE id = ?
            """, (season_id, season_name, detected_season, undertone, undertone_source, confidence, palette_json, notes, existing[0]))
            rec_id = existing[0]
        else:
            cursor.execute("""
                INSERT INTO analysis_history 
                (request_id, profile_id, season_id, season_name, detected_season, undertone, undertone_source, confidence, palette_json, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (request_id, profile_id, season_id, season_name, detected_season, undertone, undertone_source, confidence, palette_json, notes, now))
            rec_id = cursor.lastrowid
        conn.commit()
        
        cursor.execute("""
            SELECT id, request_id, profile_id, season_id, season_name, detected_season, undertone, undertone_source, confidence, palette_json, notes, created_at
            FROM analysis_history WHERE id = ?
        """, (rec_id,))
        row = dict(cursor.fetchone())
        row["palette"] = palette
        return row


def delete_history(history_id: int) -> bool:
    """Menghapus entri riwayat analisis."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM analysis_history WHERE id = ? OR request_id = ?", (history_id, str(history_id)))
        conn.commit()
        return cursor.rowcount > 0



class Database:
    """
    Database service untuk GlowMatch.

    Production menggunakan Neon PostgreSQL.
    Testing menggunakan SQLite sementara.
    """

    def __init__(
        self,
        database_url: str,
        *,
        create_schema: bool = False,
    ):
        if not database_url:
            raise ValueError("Database URL belum dikonfigurasi.")

        connect_args = {}
        engine_options = {
            "pool_pre_ping": True,
            "connect_args": connect_args,
        }

        if database_url.startswith("postgresql"):
            connect_args["connect_timeout"] = 10

        elif database_url.startswith("sqlite"):
            connect_args["check_same_thread"] = False

            if ":memory:" in database_url:
                engine_options["poolclass"] = StaticPool

        else:
            raise ValueError("Database driver tidak didukung.")

        self.engine = create_engine(
            database_url,
            **engine_options,
        )

        self.session_factory = sessionmaker(
            bind=self.engine,
            autoflush=False,
            expire_on_commit=False,
        )

        # Khusus database testing.
        # Production menggunakan Alembic.
        if create_schema:
            Base.metadata.create_all(self.engine)

    @staticmethod
    def _token_hash(token: str) -> str:
        return hashlib.sha256(
            token.encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _profile_dict(profile: Profile) -> dict:
        return {
            "id": profile.id,
            "name": profile.name,
            "gender": profile.gender,
            "age": profile.age,
            "notes": profile.notes or "",
            "is_complete": profile.is_complete,
            "created_at": (
                profile.created_at.isoformat()
                if profile.created_at else None
            ),
            "updated_at": (
                profile.updated_at.isoformat()
                if profile.updated_at else None
            ),
        }

    @staticmethod
    def _profile_snapshot(profile: Profile) -> dict:
        return {
            "name": profile.name,
            "gender": profile.gender,
            "age": profile.age,
            "notes": profile.notes or "",
        }

    def resolve_session(
        self,
        token: str | None,
        ttl_days: int = 30,
    ) -> tuple[str, int]:
        """
        Memvalidasi sesi browser atau membuat sesi baru.

        Token mentah hanya dikembalikan kepada aplikasi.
        Database hanya menyimpan hash token.
        """

        now = datetime.now(timezone.utc)

        with self.session_factory() as session:

            existing = None

            if token:
                token_hash = self._token_hash(token)

                existing = session.scalar(
                    select(UserSession).where(
                        UserSession.token_hash == token_hash
                    )
                )

            if existing:
                expires_at = existing.expires_at

                # SQLite dapat mengembalikan datetime tanpa timezone.
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(
                        tzinfo=timezone.utc
                    )

                if expires_at > now:
                    existing.last_seen_at = now
                    session.commit()

                    return token, existing.id

        

            # Buat token sesi baru.
            new_token = secrets.token_urlsafe(32)

            user_session = UserSession(
                token_hash=self._token_hash(new_token),
                created_at=now,
                expires_at=now + timedelta(days=ttl_days),
                last_seen_at=now,
            )

            session.add(user_session)
            session.flush()

            # Satu sesi memiliki satu profil.
            profile = Profile(
                session_id=user_session.id,
                name="Pengguna GlowMatch",
                gender="wanita",
                age=22,
                is_complete=False,
                notes="Profil utama",
            )

            session.add(profile)
            session.commit()

            return new_token, user_session.id

    def get_profile(self, session_id: int) -> dict:
        """Mengambil profil milik sesi pengguna."""

        with self.session_factory() as session:
            profile = session.scalar(
                select(Profile).where(
                    Profile.session_id == session_id
                )
            )

            if profile is None:
                raise LookupError("Profil pengguna tidak ditemukan.")

            return self._profile_dict(profile)

    def update_profile(
        self,
        session_id: int,
        name: str,
        gender: str = "wanita",
        age: int | None = None,
        notes: str = "",
    ) -> dict:
        """Memperbarui profil milik sesi pengguna."""

        with self.session_factory() as session:
            profile = session.scalar(
                select(Profile).where(
                    Profile.session_id == session_id
                )
            )

            if profile is None:
                raise LookupError("Profil pengguna tidak ditemukan.")

            profile.name = name
            profile.gender = gender
            profile.age = age
            profile.notes = notes or ""

            # Profil dinyatakan lengkap setelah berhasil disimpan.
            profile.is_complete = True

            profile.updated_at = datetime.now(timezone.utc)

            session.commit()
            session.refresh(profile)

            return self._profile_dict(profile)

    @staticmethod
    def _history_dict(
        history: AnalysisHistory,
        profile: Profile,
    ) -> dict:
        """Mengubah ORM history menjadi dictionary API."""

        created_at = history.created_at

        return {
            "id": history.id,
            "request_id": history.request_id,
            "profile_id": history.profile_id,
            "season_id": history.season_id,
            "season_name": history.season_name,
            "detected_season": history.detected_season,
            "undertone": history.undertone,
            "undertone_source": history.undertone_source,
            "confidence": history.confidence,
            "palette": history.palette_json or [],
            "notes": history.notes or "",
            "created_at": (
                created_at.isoformat()
                if created_at else None
            ),
            "user_name": profile.name,
            "user_gender": profile.gender,
            "user_age": profile.age,
            "analysis_result": history.analysis_result_json,
            "selected_season": history.selected_season_json,
            "profile_snapshot": history.profile_snapshot_json,
        }

    def add_history(
        self,
        session_id: int,
        season_id: str,
        season_name: str,
        undertone: str,
        request_id: str | None = None,
        detected_season: str | None = None,
        undertone_source: str = "wrist_model",
        confidence: float = 1.0,
        palette: list | None = None,
        notes: str = "",
        analysis_result: dict | None = None,
        selected_season: dict | None = None,
        profile_snapshot: dict | None = None,
    ) -> dict:
        """Menyimpan atau memperbarui hasil analisis."""

        request_id = request_id or f"gm_{uuid.uuid4().hex}"
        palette = palette or []

        with self.session_factory() as session:

            profile = session.scalar(
                select(Profile).where(
                    Profile.session_id == session_id
                )
            )

            if profile is None:
                raise LookupError("Profil pengguna tidak ditemukan.")

            history = session.scalar(
                select(AnalysisHistory).where(
                    AnalysisHistory.request_id == request_id
                )
            )

            if history and history.profile_id != profile.id:
                raise PermissionError(
                    "Request ID dimiliki pengguna lain."
                )

            if history is None:
                history = AnalysisHistory(
                    request_id=request_id,
                    profile_id=profile.id,
                )
                session.add(history)

            history.season_id = season_id
            history.season_name = season_name
            history.detected_season = detected_season
            history.undertone = undertone
            history.undertone_source = undertone_source
            history.confidence = (
                1.0 if confidence is None else confidence
            )
            history.palette_json = palette
            history.notes = notes or ""

            history.analysis_result_json = analysis_result
            history.selected_season_json = selected_season

            history.profile_snapshot_json = (
                profile_snapshot
                if profile_snapshot is not None
                else self._profile_snapshot(profile)
            )

            session.commit()
            session.refresh(history)

            return self._history_dict(history, profile)

    def get_history(
        self,
        session_id: int,
        limit: int = 50,
    ) -> list[dict]:
        """Mengambil riwayat milik sesi pengguna."""

        limit = max(1, min(limit, 100))

        with self.session_factory() as session:
            rows = session.execute(
                select(AnalysisHistory, Profile)
                .join(
                    Profile,
                    AnalysisHistory.profile_id == Profile.id,
                )
                .where(Profile.session_id == session_id)
                .order_by(
                    AnalysisHistory.created_at.desc(),
                    AnalysisHistory.id.desc(),
                )
                .limit(limit)
            ).all()

            return [
                self._history_dict(history, profile)
                for history, profile in rows
            ]

    def delete_history(
        self,
        session_id: int,
        history_id: str | int,
    ) -> bool:
        """Menghapus riwayat yang dimiliki sesi pengguna."""

        with self.session_factory() as session:

            profile = session.scalar(
                select(Profile).where(
                    Profile.session_id == session_id
                )
            )

            if profile is None:
                return False

            identifier = str(history_id)

            conditions = [
                AnalysisHistory.request_id == identifier
            ]

            if identifier.isdigit():
                conditions.append(
                    AnalysisHistory.id == int(identifier)
                )

            history = session.scalar(
                select(AnalysisHistory).where(
                    AnalysisHistory.profile_id == profile.id,
                    or_(*conditions),
                )
            )

            if history is None:
                return False

            session.delete(history)
            session.commit()

            return True

    def check_connection(self) -> bool:
        """Memeriksa koneksi database."""

        with self.engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return True

    def dispose(self) -> None:
        """Menutup koneksi database."""

        self.engine.dispose()
