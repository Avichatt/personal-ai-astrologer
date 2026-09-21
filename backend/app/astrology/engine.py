"""Astrology engine facade orchestrating coordinate resolution, ephemeris calculations, and validations."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.astrology.ephemeris import EphemerisService, ephemeris_service
from app.astrology.kp.natal import KpNatalChartEngine, KpNatalChartResult
from app.astrology.validation import ChartValidator
from app.astrology.vedic.natal import VedicNatalChartEngine, VedicNatalChartResult
from app.astrology.vedic.transits import VedicTransitCalculator, VedicTransitResult
from app.astrology.western.natal import WesternNatalChartEngine, WesternNatalChartResult
from app.astrology.western.progressions import (
    ProgressedChartResult,
    SecondaryProgressionsCalculator,
)
from app.astrology.western.transits import WesternTransitCalculator, WesternTransitResult
from app.config.constants import (
    AstrologySystem,
    Ayanamsa,
    HouseSystem,
)


class AstrologyEngine:
    """Unified facade for all astronomical, Western, Vedic, and KP chart calculations."""

    def __init__(self, ephemeris: EphemerisService | None = None) -> None:
        self.ephemeris = ephemeris or ephemeris_service
        self.validator = ChartValidator()
        self.western_engine = WesternNatalChartEngine(self.ephemeris)
        self.vedic_engine = VedicNatalChartEngine(self.ephemeris)
        self.kp_engine = KpNatalChartEngine(self.ephemeris)
        self.western_transits = WesternTransitCalculator(self.ephemeris)
        self.vedic_transits = VedicTransitCalculator(self.ephemeris)
        self.progressions = SecondaryProgressionsCalculator(self.ephemeris)

    def calculate_western_chart(
        self,
        utc_datetime: datetime,
        latitude: float,
        longitude: float,
        house_system: HouseSystem = HouseSystem.PLACIDUS,
    ) -> WesternNatalChartResult:
        """Calculate complete Western Tropical Natal Chart with aspects and balance."""
        return self.western_engine.calculate_chart(
            dt_utc=utc_datetime,
            latitude=latitude,
            longitude=longitude,
            house_system=house_system,
        )

    def calculate_vedic_chart(
        self,
        utc_datetime: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: Ayanamsa = Ayanamsa.LAHIRI,
    ) -> VedicNatalChartResult:
        """Calculate complete Vedic Sidereal Natal Chart (Kundli) with dashas and yogas."""
        return self.vedic_engine.calculate_chart(
            dt_utc=utc_datetime,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
        )

    def calculate_western_transits(
        self,
        natal_chart: WesternNatalChartResult,
        transit_utc: datetime,
        aspect_orb: float = 3.5,
    ) -> WesternTransitResult:
        """Calculate transit aspects and house overlays for Western chart."""
        return self.western_transits.calculate_transits(
            natal_planets=natal_chart.planets,
            natal_house_cusps=[h.cusp_longitude for h in natal_chart.houses],
            transit_utc=transit_utc,
            aspect_orb=aspect_orb,
        )

    def calculate_vedic_transits(
        self,
        natal_chart: VedicNatalChartResult,
        transit_utc: datetime,
        ayanamsa: Ayanamsa = Ayanamsa.LAHIRI,
    ) -> VedicTransitResult:
        """Calculate Gochar and Sade Sati for Vedic chart."""
        moon_graha = next(
            g for g in natal_chart.grahas if g.western_name == "Moon" or g.name == "Moon"
        )
        return self.vedic_transits.calculate_gochar(
            natal_moon_longitude=moon_graha.longitude,
            natal_lagna_longitude=natal_chart.ascendant_longitude,
            transit_utc=transit_utc,
            ayanamsa=ayanamsa,
        )

    def calculate_secondary_progressions(
        self,
        birth_utc: datetime,
        latitude: float,
        longitude: float,
        target_utc: datetime,
        natal_chart: WesternNatalChartResult,
        house_system: HouseSystem = HouseSystem.PLACIDUS,
    ) -> ProgressedChartResult:
        """Calculate secondary progressed chart and progressed-to-natal aspects."""
        return self.progressions.calculate_progressions(
            birth_utc=birth_utc,
            latitude=latitude,
            longitude=longitude,
            target_utc=target_utc,
            natal_planets=natal_chart.planets,
            house_system=house_system,
        )

    def calculate_kp_chart(
        self,
        utc_datetime: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: Ayanamsa = Ayanamsa.KRISHNAMURTI,
        query_datetime: datetime | None = None,
    ) -> KpNatalChartResult:
        """Calculate complete KP (Krishnamurti Paddhati) Natal Chart with sublords, significators, and ruling planets."""
        return self.kp_engine.calculate_chart(
            dt_utc=utc_datetime,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
            query_dt_utc=query_datetime,
        )

    def calculate_natal(
        self,
        utc_datetime: datetime,
        latitude: float,
        longitude: float,
        system: AstrologySystem = AstrologySystem.WESTERN,
        house_system: HouseSystem = HouseSystem.PLACIDUS,
        ayanamsa: Ayanamsa = Ayanamsa.LAHIRI,
    ) -> dict[str, Any]:
        """Generate full natal calculation dataset based on selected system."""
        if system == AstrologySystem.VEDIC:
            res = self.calculate_vedic_chart(
                utc_datetime=utc_datetime,
                latitude=latitude,
                longitude=longitude,
                ayanamsa=ayanamsa,
            )
            return res.to_dict()
        elif system == AstrologySystem.KP:
            res = self.calculate_kp_chart(
                utc_datetime=utc_datetime,
                latitude=latitude,
                longitude=longitude,
                ayanamsa=ayanamsa if ayanamsa == Ayanamsa.KRISHNAMURTI else Ayanamsa.KRISHNAMURTI,
            )
            return res.to_dict()
        else:
            res = self.calculate_western_chart(
                utc_datetime=utc_datetime,
                latitude=latitude,
                longitude=longitude,
                house_system=house_system,
            )
            return res.to_dict()


astrology_engine = AstrologyEngine()


def get_astrology_engine() -> AstrologyEngine:
    """Dependency injection provider for AstrologyEngine."""
    return astrology_engine
