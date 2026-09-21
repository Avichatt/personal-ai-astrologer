"""API endpoints for Astrological Event detection and Significance Ranking."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.astro_events.detector import AstroEventDetector
from app.astrology.engine import AstrologyEngine, get_astrology_engine
from app.database.models.user import User
from app.database.repositories.birth_profile import BirthProfileRepository
from app.schemas.event import (
    AstroEventResponse,
    EventListResponse,
    PersonalizedEventsRequest,
    UpcomingEventsRequest,
)

router = APIRouter(prefix="/events", tags=["Astro Events & Timeline"])


def get_event_detector(
    engine: Annotated[AstrologyEngine, Depends(get_astrology_engine)],
) -> AstroEventDetector:
    return AstroEventDetector(ephemeris=engine.ephemeris)


@router.post("/upcoming", response_model=EventListResponse)
async def get_upcoming_global_events(
    req: UpcomingEventsRequest,
    detector: Annotated[AstroEventDetector, Depends(get_event_detector)],
) -> EventListResponse:
    """
    Query upcoming mundane astronomical/astrological events (Eclipses, Retrogrades, Lunations, Ingresses)
    ranked dynamically by astrological significance (0-100).
    """
    events = detector.detect_mundane_events(
        start_utc=req.start_datetime_utc,
        days=req.days,
        min_score=req.min_score,
    )
    items = [
        AstroEventResponse(
            title=e.title,
            event_type=e.event_type,
            datetime_utc=e.datetime_utc,
            primary_body=e.primary_body,
            secondary_body=e.secondary_body,
            sign_name=e.sign_name,
            degree=e.degree,
            aspect_type=e.aspect_type,
            score=e.score,
            significance_tier=e.significance_tier,
            rationale=e.rationale,
            description=e.description,
        )
        for e in events
    ]
    return EventListResponse(items=items, total=len(items))


@router.post("/personalized", response_model=EventListResponse)
async def get_personalized_events(
    req: PersonalizedEventsRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    engine: Annotated[AstrologyEngine, Depends(get_astrology_engine)],
    detector: Annotated[AstroEventDetector, Depends(get_event_detector)],
) -> EventListResponse:
    """
    Query personalized transit events hitting a user's natal chart ranked by impact.
    """
    profile_repo = BirthProfileRepository(session)
    profile = await profile_repo.get_by_user_and_id(
        user_id=current_user.id,
        profile_id=req.birth_profile_id,
    )
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Birth profile {req.birth_profile_id} not found",
        )

    # Compute Western Natal planets for transit detection
    natal_chart = engine.calculate_western_chart(
        utc_datetime=profile.utc_datetime,
        latitude=profile.latitude,
        longitude=profile.longitude,
    )

    events = detector.detect_personalized_events(
        natal_planets=natal_chart.planets,
        start_utc=req.start_datetime_utc,
        days=req.days,
        min_score=req.min_score,
    )

    items = [
        AstroEventResponse(
            title=e.title,
            event_type=e.event_type,
            datetime_utc=e.datetime_utc,
            primary_body=e.primary_body,
            secondary_body=e.secondary_body,
            sign_name=e.sign_name,
            degree=e.degree,
            aspect_type=e.aspect_type,
            score=e.score,
            significance_tier=e.significance_tier,
            rationale=e.rationale,
            description=e.description,
        )
        for e in events
    ]
    return EventListResponse(items=items, total=len(items))
