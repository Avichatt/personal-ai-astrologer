"""SQLAlchemy model for persistent, versioned Natal Charts."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, ForeignKey, Index, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.database.models.birth_profile import BirthProfile
    from app.database.models.user import User


class NatalChart(Base, UUIDMixin, TimestampMixin):
    """Stores full deterministic calculated chart JSON payloads with versioning."""

    __tablename__ = "natal_charts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    birth_profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("birth_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    astrology_system: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="western",
    )
    house_system: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="placidus",
    )
    ayanamsa: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )
    engine_version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="1.0.0",
    )

    # Key Astrological Signatures (indexed for fast query / filtering)
    sun_sign: Mapped[str] = mapped_column(String(32), nullable=False)
    moon_sign: Mapped[str] = mapped_column(String(32), nullable=False)
    ascendant_sign: Mapped[str] = mapped_column(String(32), nullable=False)

    # Full structured calculation payload
    chart_data: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(postgresql.JSONB, "postgresql"),
        nullable=False,
    )

    # Relationships
    user: Mapped[User] = relationship("User", backref="natal_charts")
    birth_profile: Mapped[BirthProfile] = relationship("BirthProfile", backref="natal_charts")

    __table_args__ = (
        Index("ix_natal_charts_user_profile", "user_id", "birth_profile_id"),
        Index("ix_natal_charts_system_version", "astrology_system", "engine_version"),
    )
