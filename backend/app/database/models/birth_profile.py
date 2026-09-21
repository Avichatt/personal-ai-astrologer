from __future__ import annotations

import uuid
from datetime import date, datetime, time
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Index, String, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.database.models.user import User


class BirthProfile(Base, UUIDMixin, TimestampMixin):
    """User birth profile storing exact spatio-temporal birth parameters."""

    __tablename__ = "birth_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    local_time: Mapped[time] = mapped_column(Time, nullable=False)
    location_name: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    timezone: Mapped[str] = mapped_column(String(100), nullable=False)
    utc_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    astrology_system: Mapped[str] = mapped_column(String(20), nullable=False, default="western")
    birth_time_accuracy: Mapped[str] = mapped_column(String(20), nullable=False, default="exact")
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    user: Mapped[User] = relationship("User", back_populates="birth_profiles")

    __table_args__ = (Index("ix_birth_profiles_user_primary", "user_id", "is_primary"),)
