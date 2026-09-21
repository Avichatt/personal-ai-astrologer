"""Tests for Secondary Progressions (day-for-a-year)."""

from datetime import datetime

import pytest

from app.astrology.ephemeris import EphemerisService
from app.astrology.western.natal import WesternNatalChartEngine
from app.astrology.western.progressions import SecondaryProgressionsCalculator
from app.config.constants import HouseSystem


def test_secondary_progressions_calculation():
    ephemeris = EphemerisService()
    natal_engine = WesternNatalChartEngine(ephemeris)
    calc = SecondaryProgressionsCalculator(ephemeris)

    # Birth: 1990-01-15 13:30:00 UTC (New York)
    birth_utc = datetime(1990, 1, 15, 13, 30, 0)
    lat, lng = 40.7128, -74.0060

    natal_chart = natal_engine.calculate_chart(
        dt_utc=birth_utc,
        latitude=lat,
        longitude=lng,
        house_system=HouseSystem.PLACIDUS,
    )

    # Target: 2020-01-15 13:30:00 UTC (30 years later = exactly 30 days progressed)
    target_utc = datetime(2020, 1, 15, 13, 30, 0)

    result = calc.calculate_progressions(
        birth_utc=birth_utc,
        latitude=lat,
        longitude=lng,
        target_utc=target_utc,
        natal_planets=natal_chart.planets,
        house_system=HouseSystem.PLACIDUS,
    )

    assert pytest.approx(result.age_in_years, abs=0.1) == 30.0
    # Progressed date should be ~February 14, 1990
    assert result.progressed_datetime_utc.month == 2
    assert result.progressed_datetime_utc.year == 1990
    assert len(result.progressed_planets) == 11
    assert result.progressed_houses.ascendant >= 0.0
