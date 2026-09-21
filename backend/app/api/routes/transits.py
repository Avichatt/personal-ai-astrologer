"""API routes for planetary transits, secondary progressions, and Sade Sati."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.astrology.engine import AstrologyEngine, get_astrology_engine
from app.database.models.user import User
from app.database.repositories.birth_profile import BirthProfileRepository
from app.schemas.transit import (
    CurrentTransitRequest,
    ProfileTransitRequest,
    SecondaryProgressionRequest,
)

router = APIRouter(prefix="/transits", tags=["Transits & Progressions"])


@router.post("/current", response_model=dict[str, Any])
async def get_current_sky_transits(
    req: CurrentTransitRequest,
    engine: Annotated[AstrologyEngine, Depends(get_astrology_engine)],
) -> dict[str, Any]:
    """Get real-time snapshot of current planetary positions in Tropical and Sidereal zodiacs."""
    western_chart = engine.calculate_western_chart(
        utc_datetime=req.target_datetime_utc,
        latitude=0.0,
        longitude=0.0,
    )
    vedic_chart = engine.calculate_vedic_chart(
        utc_datetime=req.target_datetime_utc,
        latitude=0.0,
        longitude=0.0,
        ayanamsa=req.ayanamsa,
    )

    return {
        "datetime_utc": req.target_datetime_utc.isoformat(),
        "western": western_chart.to_dict(),
        "vedic": vedic_chart.to_dict(),
    }


@router.post("/profile", response_model=dict[str, Any])
async def calculate_profile_transits(
    req: ProfileTransitRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    engine: Annotated[AstrologyEngine, Depends(get_astrology_engine)],
) -> dict[str, Any]:
    """Calculate real-time transits, aspects, and house overlays for a saved user birth profile."""
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

    # Compute Western Natal & Transits
    western_natal = engine.calculate_western_chart(
        utc_datetime=profile.utc_datetime,
        latitude=profile.latitude,
        longitude=profile.longitude,
    )
    western_transits = engine.calculate_western_transits(
        natal_chart=western_natal,
        transit_utc=req.target_datetime_utc,
        aspect_orb=req.aspect_orb,
    )

    # Compute Vedic Natal & Gochar / Sade Sati
    vedic_natal = engine.calculate_vedic_chart(
        utc_datetime=profile.utc_datetime,
        latitude=profile.latitude,
        longitude=profile.longitude,
    )
    vedic_transits = engine.calculate_vedic_transits(
        natal_chart=vedic_natal,
        transit_utc=req.target_datetime_utc,
    )

    return {
        "birth_profile_id": str(profile.id),
        "target_datetime_utc": req.target_datetime_utc.isoformat(),
        "western_transits": {
            "transit_to_natal_aspects": [
                asdict_like(a) for a in western_transits.transit_to_natal_aspects
            ],
            "transits_in_natal_houses": [
                asdict_like(h) for h in western_transits.transits_in_natal_houses
            ],
        },
        "vedic_gochar": vedic_transits.to_dict(),
    }


@router.post("/progressions", response_model=dict[str, Any])
async def calculate_profile_progressions(
    req: SecondaryProgressionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    engine: Annotated[AstrologyEngine, Depends(get_astrology_engine)],
) -> dict[str, Any]:
    """Calculate secondary progressed chart and progressed-to-natal aspects for a profile."""
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

    western_natal = engine.calculate_western_chart(
        utc_datetime=profile.utc_datetime,
        latitude=profile.latitude,
        longitude=profile.longitude,
    )

    progressions = engine.calculate_secondary_progressions(
        birth_utc=profile.utc_datetime,
        latitude=profile.latitude,
        longitude=profile.longitude,
        target_utc=req.target_datetime_utc,
        natal_chart=western_natal,
    )

    from dataclasses import asdict

    return {
        "birth_profile_id": str(profile.id),
        "age_in_years": progressions.age_in_years,
        "progressed_datetime_utc": progressions.progressed_datetime_utc.isoformat(),
        "target_datetime_utc": progressions.target_datetime_utc.isoformat(),
        "progressed_planets": [asdict(p) for p in progressions.progressed_planets],
        "progressed_to_natal_aspects": [
            {
                **asdict(a),
                "aspect_type": a.aspect_type.value,
            }
            for a in progressions.progressed_to_natal_aspects
        ],
    }


def asdict_like(obj: Any) -> dict:
    from dataclasses import asdict, is_dataclass

    if is_dataclass(obj):
        d = asdict(obj)
        if "aspect_type" in d and hasattr(d["aspect_type"], "value"):
            d["aspect_type"] = d["aspect_type"].value
        return d
    return dict(obj)
