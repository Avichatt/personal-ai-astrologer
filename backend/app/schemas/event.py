"""Pydantic schemas for Astrological Events and Ranking endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.astro_events.significance import EventSignificanceTier
from app.config.constants import AstroEventType


class AstroEventResponse(BaseModel):
    """Standardized event item in API responses."""

    title: str
    event_type: AstroEventType
    datetime_utc: datetime
    primary_body: str
    secondary_body: str | None = None
    sign_name: str | None = None
    degree: float | None = None
    aspect_type: str | None = None
    score: float
    significance_tier: EventSignificanceTier
    rationale: str
    description: str


class UpcomingEventsRequest(BaseModel):
    """Parameters to query upcoming global events."""

    start_datetime_utc: datetime = Field(default_factory=datetime.utcnow)
    days: int = Field(default=30, ge=1, le=365)
    min_score: float = Field(default=0.0, ge=0.0, le=100.0)


class PersonalizedEventsRequest(BaseModel):
    """Parameters to query upcoming events personalized for a birth profile."""

    birth_profile_id: uuid.UUID
    start_datetime_utc: datetime = Field(default_factory=datetime.utcnow)
    days: int = Field(default=30, ge=1, le=365)
    min_score: float = Field(default=0.0, ge=0.0, le=100.0)


class EventListResponse(BaseModel):
    """List of detected astrological events."""

    items: list[AstroEventResponse]
    total: int
