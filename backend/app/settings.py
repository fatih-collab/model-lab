"""Konfigurasi lewat environment variable (prefix GLOWMATCH_). Diimpor paling awal oleh app.main."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]


def _env(name: str, default: str) -> str:
    return os.environ.get(f"GLOWMATCH_{name}", default)


def _flag(name: str, default: bool) -> bool:
    return _env(name, "1" if default else "0").strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Settings:
    models_dir: Path = field(default_factory=lambda: Path(_env("MODELS_DIR", str(BACKEND_DIR / "models"))))
    load_models: bool = field(default_factory=lambda: _flag("LOAD_MODELS", True))
    device: str = field(default_factory=lambda: _env("DEVICE", "auto"))              # auto | cpu | cuda
    torch_threads: int = field(default_factory=lambda: int(_env("TORCH_THREADS", "0")))  # 0 = bawaan torch
    max_folds: int = field(default_factory=lambda: int(_env("MAX_FOLDS", "0")))      # 0 = semua fold (sesuai training)
    white_balance: bool = field(default_factory=lambda: _flag("WHITE_BALANCE", True))
    wb_strength: float = field(default_factory=lambda: float(_env("WB_STRENGTH", "1.0")))
    max_upload_mb: float = field(default_factory=lambda: float(_env("MAX_UPLOAD_MB", "8")))
    cors_origins: tuple[str, ...] = field(default_factory=lambda: tuple(
        o.strip() for o in _env("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o.strip()))


settings = Settings()

# Bobot Hugging Face (DINOv2 via timm, DINOv3, SegFormer) dibaca dari cache proyek yang diisi
# `scripts/extract_models.py fetch`. Harus di-set sebelum timm/transformers diimpor.
os.environ.setdefault("HF_HUB_CACHE", str(settings.models_dir / "hf_cache" / "hub"))
