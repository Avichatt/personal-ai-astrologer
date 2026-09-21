"""API endpoints for AI Horoscope Interpretation and Precision Astrological Readings."""

from __future__ import annotations

from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.astrology.engine import AstrologyEngine, get_astrology_engine
from app.config.constants import AstrologySystem
from app.database.models.user import User
from app.database.repositories.birth_profile import BirthProfileRepository
from app.schemas.analysis import (
    AnalysisFocus,
    DirectAnalysisRequest,
    HoroscopeAnalysisResponse,
    ProfileAnalysisRequest,
)
from app.services.ai_interpretation import (
    AstroInterpretationService,
    get_astro_interpretation_service,
)

router = APIRouter(prefix="/analysis", tags=["Horoscope Analysis"])


@router.post("/horoscope", response_model=HoroscopeAnalysisResponse)
async def generate_horoscope_analysis(
    req: DirectAnalysisRequest,
    engine: Annotated[AstrologyEngine, Depends(get_astrology_engine)],
    service: Annotated[AstroInterpretationService, Depends(get_astro_interpretation_service)],
) -> HoroscopeAnalysisResponse:
    """Generate structured horoscope interpretation with Parashari deductions and timelines.

    Accepts raw birth coordinates and timestamp. Available to explore on demand.
    """
    chart_dict = engine.calculate_natal(
        utc_datetime=req.utc_datetime,
        latitude=req.latitude,
        longitude=req.longitude,
        system=req.system,
        house_system=req.house_system,
        ayanamsa=req.ayanamsa,
    )

    return service.generate_analysis(
        chart_dict=chart_dict,
        focus=req.focus,
        target_date=req.target_date,
        name=req.name,
        system=req.system,
        language=req.language,
    )


@router.post("/profile", response_model=HoroscopeAnalysisResponse)
async def generate_profile_horoscope_analysis(
    req: ProfileAnalysisRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    engine: Annotated[AstrologyEngine, Depends(get_astrology_engine)],
    service: Annotated[AstroInterpretationService, Depends(get_astro_interpretation_service)],
) -> HoroscopeAnalysisResponse:
    """Generate structured horoscope interpretation for a saved user birth profile."""
    repo = BirthProfileRepository(session)
    profile = await repo.get_by_user_and_id(
        user_id=current_user.id,
        profile_id=req.birth_profile_id,
    )
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Birth profile {req.birth_profile_id} not found.",
        )

    chart_dict = engine.calculate_natal(
        utc_datetime=profile.utc_datetime,
        latitude=profile.latitude,
        longitude=profile.longitude,
        system=req.system,
        house_system=req.house_system,
        ayanamsa=req.ayanamsa,
    )

    return service.generate_analysis(
        chart_dict=chart_dict,
        focus=req.focus,
        target_date=req.target_date,
        name=getattr(profile, "name", "Native") or "Native",
        system=req.system,
        language=req.language,
    )


@router.post("/life-blueprint", response_model=HoroscopeAnalysisResponse)
async def generate_life_blueprint(
    req: DirectAnalysisRequest,
    engine: Annotated[AstrologyEngine, Depends(get_astrology_engine)],
    service: Annotated[AstroInterpretationService, Depends(get_astro_interpretation_service)],
) -> HoroscopeAnalysisResponse:
    """Generate complete professional Birth-to-Death Life Blueprint.

    Covers birth chart foundation, 5 chronological life stages (0-18, 18-30, 30-50, 50-65, 65+),
    technical yogas & strengths, vargas (D1, D9, D10), gemstone prescriptions, and spiritual remedies.
    """
    chart_dict = engine.calculate_natal(
        utc_datetime=req.utc_datetime,
        latitude=req.latitude,
        longitude=req.longitude,
        system=req.system,
        house_system=req.house_system,
        ayanamsa=req.ayanamsa,
    )

    return service.generate_analysis(
        chart_dict=chart_dict,
        focus=AnalysisFocus.LIFE_BLUEPRINT,
        target_date=req.target_date,
        name=req.name,
        system=req.system,
        language=req.language,
    )

