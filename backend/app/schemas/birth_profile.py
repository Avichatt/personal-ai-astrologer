"""Birth profile Pydantic request and response schemas."""

from __future__ import annotations

import uuid
from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class BirthProfileCreate(BaseModel):
    """Payload to create a new birth profile."""

    name: str = Field(..., min_length=1, max_length=100, description="Name of the person")
    date_of_birth: date = Field(..., description="Date of birth (YYYY-MM-DD)")
    local_time: time = Field(..., description="Local clock time of birth (HH:MM:SS)")
    location_name: str = Field(
        ..., min_length=2, max_length=255, description="Full birth location query"
    )
    city: str | None = Field(None, max_length=100)
    country: str | None = Field(None, max_length=100)
    latitude: float | None = Field(
        None, ge=-90.0, le=90.0, description="Latitude in decimal degrees"
    )
    longitude: float | None = Field(
        None, ge=-180.0, le=180.0, description="Longitude in decimal degrees"
    )
    timezone: str | None = Field(None, max_length=100, description="IANA timezone name")
    astrology_system: Literal["western", "vedic"] = Field(
        default="western", description="Preferred astrological system"
    )
    birth_time_accuracy: Literal["exact", "approximate", "unknown"] = Field(
        default="exact", description="Confidence level of birth time"
    )
    is_primary: bool = Field(
        default=False, description="Whether this is the user's primary chart profile"
    )

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: date) -> date:
        if v.year < 1800 or v.year > 2100:
            raise ValueError("Birth year must be between 1800 and 2100")
        return v


class BirthProfileUpdate(BaseModel):
    """Payload to update an existing birth profile."""

    name: str | None = Field(None, min_length=1, max_length=100)
    date_of_birth: date | None = None
    local_time: time | None = None
    location_name: str | None = Field(None, min_length=2, max_length=255)
    city: str | None = None
    country: str | None = None
    latitude: float | None = Field(None, ge=-90.0, le=90.0)
    longitude: float | None = Field(None, ge=-180.0, le=180.0)
    timezone: str | None = None
    astrology_system: Literal["western", "vedic"] | None = None
    birth_time_accuracy: Literal["exact", "approximate", "unknown"] | None = None
    is_primary: bool | None = None


class BirthProfileResponse(BaseModel):
    """Response model for a birth profile."""

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    date_of_birth: date
    local_time: time
    location_name: str
    city: str | None
    country: str | None
    latitude: float
    longitude: float
    timezone: str
    utc_datetime: datetime
    astrology_system: str
    birth_time_accuracy: str
    is_primary: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
