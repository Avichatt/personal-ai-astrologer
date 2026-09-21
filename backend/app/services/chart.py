"""Service orchestrating Natal Chart calculation, persistence, and versioning."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.astrology.engine import AstrologyEngine, get_astrology_engine
from app.config.constants import AstrologySystem, Ayanamsa, HouseSystem
from app.database.models.natal_chart import NatalChart
from app.database.repositories.birth_profile import BirthProfileRepository
from app.database.repositories.natal_chart import NatalChartRepository
from app.schemas.chart import (
    ChartCreateRequest,
    ChartRecalculateRequest,
    EphemeralCalculateRequest,
)

CURRENT_ENGINE_VERSION = "1.0.0"


class ChartService:
    """Application service for astrology chart operations."""

    def __init__(
        self,
        session: AsyncSession,
        engine: AstrologyEngine | None = None,
    ) -> None:
        self.session = session
        self.chart_repo = NatalChartRepository(session)
        self.profile_repo = BirthProfileRepository(session)
        self.engine = engine or get_astrology_engine()

    def calculate_ephemeral(self, req: EphemeralCalculateRequest) -> dict[str, Any]:
        """Perform on-demand calculation without database persistence."""
        return self.engine.calculate_natal(
            utc_datetime=req.utc_datetime,
            latitude=req.latitude,
            longitude=req.longitude,
            system=req.astrology_system,
            house_system=req.house_system,
            ayanamsa=req.ayanamsa,
        )

    async def create_chart_for_profile(
        self,
        user_id: uuid.UUID,
        req: ChartCreateRequest,
    ) -> NatalChart:
        """Calculate and save a new NatalChart linked to a BirthProfile."""
        profile = await self.profile_repo.get_by_user_and_id(
            user_id=user_id,
            profile_id=req.birth_profile_id,
        )
        if not profile:
            raise ValueError(f"BirthProfile {req.birth_profile_id} not found.")

        # Calculate using engine
        chart_dict = self.engine.calculate_natal(
            utc_datetime=profile.utc_datetime,
            latitude=profile.latitude,
            longitude=profile.longitude,
            system=req.astrology_system,
            house_system=req.house_system,
            ayanamsa=req.ayanamsa,
        )

        # Extract primary signs for index
        if req.astrology_system == AstrologySystem.VEDIC:
            sun_sign = next(
                (
                    g["rashi_name"]
                    for g in chart_dict.get("grahas", [])
                    if g["western_name"] == "Sun" or g["name"] == "Sun"
                ),
                "Mesha",
            )
            moon_sign = next(
                (
                    g["rashi_name"]
                    for g in chart_dict.get("grahas", [])
                    if g["western_name"] == "Moon" or g["name"] == "Moon"
                ),
                "Mesha",
            )
            ascendant_sign = chart_dict.get("ascendant_rashi", "Mesha")
        else:
            sun_sign = chart_dict.get("sun_sign", "Aries")
            moon_sign = chart_dict.get("moon_sign", "Aries")
            ascendant_sign = chart_dict.get("ascendant_sign", "Aries")

        return await self.chart_repo.create(
            user_id=user_id,
            birth_profile_id=profile.id,
            astrology_system=req.astrology_system.value,
            house_system=req.house_system.value,
            ayanamsa=req.ayanamsa.value if req.astrology_system == AstrologySystem.VEDIC else None,
            engine_version=CURRENT_ENGINE_VERSION,
            sun_sign=sun_sign,
            moon_sign=moon_sign,
            ascendant_sign=ascendant_sign,
            chart_data=chart_dict,
        )

    async def get_chart(
        self,
        user_id: uuid.UUID,
        chart_id: uuid.UUID,
    ) -> NatalChart | None:
        """Fetch a saved chart guaranteeing user isolation."""
        return await self.chart_repo.get_by_user_and_id(user_id=user_id, chart_id=chart_id)

    async def list_charts_for_profile(
        self,
        user_id: uuid.UUID,
        profile_id: uuid.UUID,
    ) -> list[NatalChart]:
        """List all charts for a given profile."""
        charts = await self.chart_repo.list_by_profile_id(
            user_id=user_id,
            birth_profile_id=profile_id,
        )
        return list(charts)

    async def recalculate_chart(
        self,
        user_id: uuid.UUID,
        chart_id: uuid.UUID,
        req: ChartRecalculateRequest,
    ) -> NatalChart:
        """Recalculate an existing chart with updated parameters or engine version."""
        chart = await self.get_chart(user_id, chart_id)
        if not chart:
            raise ValueError(f"NatalChart {chart_id} not found.")

        profile = await self.profile_repo.get_by_user_and_id(user_id, chart.birth_profile_id)
        if not profile:
            raise ValueError("Associated BirthProfile not found.")

        system = AstrologySystem(chart.astrology_system)
        house_system = req.house_system or HouseSystem(chart.house_system)
        ayanamsa = req.ayanamsa or (Ayanamsa(chart.ayanamsa) if chart.ayanamsa else Ayanamsa.LAHIRI)

        chart_dict = self.engine.calculate_natal(
            utc_datetime=profile.utc_datetime,
            latitude=profile.latitude,
            longitude=profile.longitude,
            system=system,
            house_system=house_system,
            ayanamsa=ayanamsa,
        )

        if system == AstrologySystem.VEDIC:
            sun_sign = next(
                (
                    g["rashi_name"]
                    for g in chart_dict.get("grahas", [])
                    if g["western_name"] == "Sun" or g["name"] == "Sun"
                ),
                "Mesha",
            )
            moon_sign = next(
                (
                    g["rashi_name"]
                    for g in chart_dict.get("grahas", [])
                    if g["western_name"] == "Moon" or g["name"] == "Moon"
                ),
                "Mesha",
            )
            asc_sign = chart_dict.get("ascendant_rashi", "Mesha")
        else:
            sun_sign = chart_dict.get("sun_sign", "Aries")
            moon_sign = chart_dict.get("moon_sign", "Aries")
            asc_sign = chart_dict.get("ascendant_sign", "Aries")

        updated = await self.chart_repo.update(
            chart.id,
            house_system=house_system.value,
            ayanamsa=ayanamsa.value if system == AstrologySystem.VEDIC else None,
            engine_version=CURRENT_ENGINE_VERSION,
            sun_sign=sun_sign,
            moon_sign=moon_sign,
            ascendant_sign=asc_sign,
            chart_data=chart_dict,
        )
        if not updated:
            raise ValueError(f"Failed to update chart {chart_id}")
        return updated
