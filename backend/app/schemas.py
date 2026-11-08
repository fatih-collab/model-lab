"""Skema respons API (dokumentasi OpenAPI di /docs + validasi keluaran)."""
from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import (
    BaseModel as _BaseModel,
    ConfigDict,
    Field,
)


class BaseModel(_BaseModel):
    model_config = ConfigDict(protected_namespaces=())        # field model_probability / model_choice


class Color(BaseModel):
    name: str
    hex: str


class PaletteGroups(BaseModel):
    utama: list[Color]
    netral: list[Color]
    hindari: list[Color]


class Palette(BaseModel):
    description: str
    keywords: list[str]
    palettes: PaletteGroups


class WhiteBalance(BaseModel):
    gains_bgr: tuple[float, float, float]
    source: str
    ref_fraction: float
    neutral_fraction: float
    clipped: bool


class Quality(BaseModel):
    ok: bool
    kind: Literal["face", "wrist"]
    box: Optional[list[float]] = None          # (x, y, w, h) wajah pada frame asli -> posisi cincin palet
    crop_box: Optional[list[int]] = None
    frame_size: list[int]
    white_balance: WhiteBalance
    issues: list[str]
    warnings: list[str]
    messages: list[str]
    metrics: dict[str, float]
    ms: Optional[float] = None


class SeasonOption(BaseModel):
    id: str
    name: str
    family: str
    undertone: str
    probability: float
    model_probability: float
    relation: str
    matches_undertone: bool


class SeasonWithPalette(SeasonOption):
    palette: Palette


class FinalSeason(SeasonWithPalette):
    confidence_status: Literal["yakin", "perlu_konfirmasi"]


class Gate(BaseModel):
    undertone: Literal["warm", "cool", "neutral"]
    undertone_source: Literal["wrist_model", "season_model"]
    applied: bool
    rule: str
    allowed_families: list[str]
    model_choice: str
    overridden: bool
    conflict: bool
    season_p_warm: float
    lean: Literal["warm", "cool"]


class Undertone(BaseModel):
    label: Literal["cool", "neutral", "warm"]
    probs: Optional[dict[str, float]] = None
    confidence: Optional[float] = None
    components: dict[str, dict[str, float]] = {}
    source: Literal["wrist_model", "client"]


class AnalysisResult(BaseModel):
    season: FinalSeason
    neighbors: list[SeasonWithPalette]
    gate: Gate
    ranking: list[SeasonOption]
    candidates: list[str]


class QualityPair(BaseModel):
    face: Optional[Quality] = None
    wrist: Optional[Quality] = None


class AnalyzeResponse(BaseModel):
    status: Literal["ok", "rejected"]
    request_id: Optional[str] = None
    stage: Optional[Literal["face", "wrist"]] = None        # hanya bila rejected
    messages: list[str] = []
    result: Optional[AnalysisResult] = None
    undertone: Optional[Undertone] = None
    quality: QualityPair
    timings_ms: dict[str, float] = {}
    debug: Optional[dict] = None


class UndertoneResponse(BaseModel):
    status: Literal["ok", "rejected"]
    request_id: Optional[str] = None
    stage: Optional[Literal["wrist"]] = None
    messages: list[str] = []
    undertone: Optional[Undertone] = None
    quality: QualityPair
    timings_ms: dict[str, float] = {}


class Health(BaseModel):
    status: Literal["ok", "degraded"]
    undertone_ready: bool
    season_ready: bool
    device: str
    detector: str
    white_balance: bool
    load_errors: dict[str, str]


class SeasonInfo(BaseModel):
    id: str
    name: str
    family: str
    subtype: str
    undertone: str
    neighbors: list[str]
    palette: Palette


class Profile(BaseModel):
    """
    Informasi profil pengguna GlowMatch.
    """

    id: int
    name: str
    gender: str = "wanita"
    age: Optional[int] = 22
    notes: Optional[str] = ""
    is_complete: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ProfileUpdate(BaseModel):
    """
    Request untuk memperbarui profil pengguna.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    name: str = Field(
        min_length=1,
        max_length=120,
    )

    gender: str = Field(
        default="wanita",
        min_length=1,
        max_length=20,
    )

    age: int = Field(
        default=22,
        ge=5,
        le=100,
    )

    notes: Optional[str] = ""


class HistoryItem(BaseModel):
    """
    Data riwayat analisis yang dikembalikan API.

    Selain ringkasan, schema ini menyediakan snapshot
    agar hasil analisis lama dapat ditampilkan kembali
    dan digunakan untuk menghasilkan laporan PDF.
    """

    id: int
    request_id: Optional[str] = None
    profile_id: Optional[int] = None

    # Ringkasan hasil analisis.
    season_id: str
    season_name: str
    detected_season: Optional[str] = None

    undertone: str
    undertone_source: Optional[str] = "wrist_model"
    confidence: Optional[float] = 1.0

    palette: list[str] = Field(default_factory=list)
    notes: Optional[str] = ""

    created_at: Optional[str] = None

    # Snapshot informasi profil saat analisis dilakukan.
    user_name: Optional[str] = None
    user_gender: Optional[str] = None
    user_age: Optional[int] = None

    # Snapshot hasil klasifikasi lengkap.
    analysis_result: Optional[dict[str, Any]] = None

    # Snapshot season atau rekomendasi yang dipilih.
    selected_season: Optional[dict[str, Any]] = None

    # Snapshot profil pada saat analisis dilakukan.
    profile_snapshot: Optional[dict[str, Any]] = None


class HistoryCreate(BaseModel):
    """
    Request untuk menyimpan hasil analisis GlowMatch.

    profile_id tetap dipertahankan untuk kompatibilitas
    request lama, tetapi backend tidak menggunakannya
    sebagai penentu kepemilikan data.
    """

    season_id: str
    season_name: str
    undertone: str

    request_id: Optional[str] = None
    detected_season: Optional[str] = None
    undertone_source: Optional[str] = "wrist_model"
    confidence: Optional[float] = 1.0

    palette: list[str] = Field(default_factory=list)
    notes: Optional[str] = ""

    # Data hasil analisis lengkap.
    analysis_result: Optional[dict[str, Any]] = None

    # Data rekomendasi season yang dipilih pengguna.
    selected_season: Optional[dict[str, Any]] = None

    # Field lama dipertahankan untuk kompatibilitas.
    # Kepemilikan tetap ditentukan dari session cookie.
    profile_id: Optional[int] = None

