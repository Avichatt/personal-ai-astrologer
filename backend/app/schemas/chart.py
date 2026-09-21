"""Pydantic request and response schemas for Natal Chart calculation and persistence."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.config.constants import AstrologySystem, Ayanamsa, HouseSystem


class EphemeralCalculateRequest(BaseModel):
    """Direct on-demand chart calculation request without requiring a saved profile."""

    utc_datetime: datetime = Field(..., description="UTC date and time of birth/event")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees")
    astrology_system: AstrologySystem = Field(default=AstrologySystem.WESTERN)
    house_system: HouseSystem = Field(default=HouseSystem.PLACIDUS)
    ayanamsa: Ayanamsa = Field(default=Ayanamsa.LAHIRI)


class ChartCreateRequest(BaseModel):
    """Calculate and save a Natal Chart for an existing BirthProfile."""

    birth_profile_id: uuid.UUID
    astrology_system: AstrologySystem = Field(default=AstrologySystem.WESTERN)
    house_system: HouseSystem = Field(default=HouseSystem.PLACIDUS)
    ayanamsa: Ayanamsa = Field(default=Ayanamsa.LAHIRI)


class ChartRecalculateRequest(BaseModel):
    """Recalculate an existing chart with updated parameters or engine version."""

    house_system: HouseSystem | None = None
    ayanamsa: Ayanamsa | None = None


class NatalChartResponse(BaseModel):
    """Structured response for a saved Natal Chart entity."""

    id: uuid.UUID
    user_id: uuid.UUID
    birth_profile_id: uuid.UUID
    astrology_system: str
    house_system: str
    ayanamsa: str | None
    engine_version: str
    sun_sign: str
    moon_sign: str
    ascendant_sign: str
    chart_data: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChartListResponse(BaseModel):
    """List of charts for a birth profile."""

    items: list[NatalChartResponse]
    total: int
