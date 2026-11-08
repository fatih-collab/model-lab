
"""
Konfigurasi GlowMatch melalui environment variable.

Semua konfigurasi menggunakan prefix GLOWMATCH_.
File .env pada root repository dibaca untuk development lokal.

Pengaturan Hugging Face cache harus disiapkan sebelum
library timm atau transformers diimpor.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


# ============================================================
# 1. DIREKTORI PROJECT
# ============================================================

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent


# ============================================================
# 2. LOAD ENVIRONMENT VARIABLE
# ============================================================

# Membaca file .env pada root repository:
# C:/SEMESTER 5/glowmatch/.env
#
# override=False berarti environment variable sistem
# tetap memiliki prioritas jika sudah didefinisikan.

ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=ENV_FILE, override=False)


# ============================================================
# 3. HELPER ENVIRONMENT VARIABLE
# ============================================================

def _env(name: str, default: str) -> str:
    """
    Mengambil environment variable dengan prefix GLOWMATCH_.
    """
    return os.environ.get(f"GLOWMATCH_{name}", default)


def _flag(name: str, default: bool) -> bool:
    """
    Mengambil konfigurasi boolean dari environment variable.
    """
    return _env(
        name,
        "1" if default else "0"
    ).strip().lower() in ("1", "true", "yes", "on")


# ============================================================
# 4. APPLICATION SETTINGS
# ============================================================

@dataclass(frozen=True)
class Settings:

    # --------------------------------------------------------
    # Machine Learning Configuration
    # --------------------------------------------------------

    models_dir: Path = field(
        default_factory=lambda: Path(
            _env("MODELS_DIR", str(BACKEND_DIR / "models"))
        )
    )

    load_models: bool = field(
        default_factory=lambda: _flag("LOAD_MODELS", True)
    )

    device: str = field(
        default_factory=lambda: _env("DEVICE", "auto")
    )

    torch_threads: int = field(
        default_factory=lambda: int(_env("TORCH_THREADS", "0"))
    )

    max_folds: int = field(
        default_factory=lambda: int(_env("MAX_FOLDS", "0"))
    )

    white_balance: bool = field(
        default_factory=lambda: _flag("WHITE_BALANCE", True)
    )

    wb_strength: float = field(
        default_factory=lambda: float(_env("WB_STRENGTH", "1.0"))
    )

    max_upload_mb: float = field(
        default_factory=lambda: float(_env("MAX_UPLOAD_MB", "8"))
    )

    # --------------------------------------------------------
    # PostgreSQL Database Configuration
    # --------------------------------------------------------

    # Koneksi utama aplikasi menggunakan role glowmatch.
    database_url: str = field(
        default_factory=lambda: _env("DATABASE_URL", "")
    )

    # Koneksi administratif untuk proses migration.
    migration_database_url: str = field(
        default_factory=lambda: _env("MIGRATION_DATABASE_URL", "")
    )

    # --------------------------------------------------------
    # API Configuration
    # --------------------------------------------------------

    cors_origins: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            origin.strip()
            for origin in _env(
                "CORS_ORIGINS",
                "http://localhost:5173,http://127.0.0.1:5173"
            ).split(",")
            if origin.strip()
        )
    )


# ============================================================
# 5. INITIALIZE SETTINGS
# ============================================================

settings = Settings()


# ============================================================
# 6. HUGGING FACE CACHE CONFIGURATION
# ============================================================

# Harus disetel sebelum timm/transformers diimpor.

os.environ.setdefault(
    "HF_HUB_CACHE",
    str(settings.models_dir / "hf_cache" / "hub")
)
