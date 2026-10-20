"""
Database SQLite untuk GlowMatch — profil pengguna dan riwayat analisis.
File database disimpan di backend/glowmatch.db (atau sesuai GLOWMATCH_DB_PATH).
"""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

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
