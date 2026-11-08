
"""
SQLAlchemy ORM models for GlowMatch.
Database utama: PostgreSQL (Neon).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# JSON untuk pengujian SQLite dan JSONB untuk PostgreSQL.
JSONDocument = JSON().with_variant(JSONB, "postgresql")


class Base(DeclarativeBase):
    """Base class seluruh model SQLAlchemy."""


class UserSession(Base):
    """Identitas sesi browser pengguna."""

    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    # SHA-256 hash dari token sesi, bukan token mentah.
    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    profile: Mapped[Profile | None] = relationship(
        back_populates="session",
        uselist=False,
        cascade="all, delete-orphan",
    )


class Profile(Base):
    """Profil personal color pengguna."""

    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    session_id: Mapped[int] = mapped_column(
        ForeignKey("user_sessions.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        default="Pengguna GlowMatch",
        server_default=text("'Pengguna GlowMatch'"),
    )

    gender: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="wanita",
        server_default=text("'wanita'"),
    )

    age: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=22,
        server_default=text("22"),
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default="",
        server_default=text("''"),
    )

    is_complete: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    session: Mapped[UserSession] = relationship(
        back_populates="profile",
    )

    history: Mapped[list[AnalysisHistory]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class AnalysisHistory(Base):
    """Riwayat analisis personal color pengguna."""

    __tablename__ = "analysis_history"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    request_id: Mapped[str | None] = mapped_column(
        String(128),
        unique=True,
        nullable=True,
    )

    profile_id: Mapped[int] = mapped_column(
    ForeignKey("profiles.id", ondelete="CASCADE"),
    nullable=False,
    )

    season_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    season_name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    detected_season: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )

    undertone: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    undertone_source: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="wrist_model",
        server_default=text("'wrist_model'"),
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
        server_default=text("1.0"),
    )

    palette_json: Mapped[list[Any]] = mapped_column(
        JSONDocument,
        nullable=False,
        default=list,
        server_default=text("'[]'"),
    )

    # Snapshot hasil lengkap dari AnalysisResponse.
    analysis_result_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSONDocument,
        nullable=True,
    )

    # Snapshot season/rekomendasi yang dipilih pengguna.
    selected_season_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSONDocument,
        nullable=True,
    )

    # Snapshot profil pada saat analisis dilakukan.
    profile_snapshot_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSONDocument,
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default="",
        server_default=text("''"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    profile: Mapped[Profile] = relationship(
        back_populates="history",
    )

    __table_args__ = (
        Index(
            "ix_analysis_history_profile_created_at",
            "profile_id",
            "created_at",
        ),
    )
