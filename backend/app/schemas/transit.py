"""Pydantic request and response schemas for Transit endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.config.constants import Ayanamsa


class CurrentTransitRequest(BaseModel):
    """Query parameters for current or target date planetary transit snapshot."""

    target_datetime_utc: datetime = Field(default_factory=datetime.utcnow)
    ayanamsa: Ayanamsa = Field(default=Ayanamsa.LAHIRI)


class ProfileTransitRequest(BaseModel):
    """Calculate transits against a specific saved Birth Profile."""

    birth_profile_id: uuid.UUID
    target_datetime_utc: datetime = Field(default_factory=datetime.utcnow)
    aspect_orb: float = Field(default=3.5, ge=0.5, le=10.0)


class SecondaryProgressionRequest(BaseModel):
    """Calculate secondary progressions against a specific saved Birth Profile."""

    birth_profile_id: uuid.UUID
    target_datetime_utc: datetime = Field(default_factory=datetime.utcnow)
