"""Tests for the EphemerisService and AstrologyEngine against golden reference charts."""

from datetime import UTC, datetime

import pytest

from app.astrology.engine import AstrologyEngine
from app.astrology.ephemeris import EphemerisService
from app.config.constants import AstrologySystem, Ayanamsa, HouseSystem
from tests.golden_charts import GOLDEN_CHARTS


@pytest.fixture
def ephe_service():
    return EphemerisService()


@pytest.fixture
def astro_engine():
    return AstrologyEngine()


def test_julian_day_calculation(ephe_service):
    # J2000.0 epoch: 2000-01-01 12:00:00 UTC = 2451545.0
    dt = datetime(2000, 1, 1, 12, 0, 0, tzinfo=UTC)
    jd = ephe_service.datetime_to_julian_day(dt)
    assert jd == pytest.approx(2451545.0, abs=0.001)


def test_ayanamsa_calculation(ephe_service):
    # Year 2000 Lahiri ayanamsa is approx 23.85°
    jd = 2451545.0
    val = ephe_service.get_ayanamsa_value(jd, Ayanamsa.LAHIRI)
    assert 23.5 < val < 24.5


def test_calculate_all_planets_structure(ephe_service):
    dt = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)
    jd = ephe_service.datetime_to_julian_day(dt)
    planets = ephe_service.calculate_all_planets(jd)

    assert "Sun" in planets
    assert "Moon" in planets
    assert "Mars" in planets
    assert "Ketu" in planets
    assert 0.0 <= planets["Sun"].longitude < 360.0
    assert 0 <= planets["Sun"].sign_index <= 11


def test_calculate_houses_structure(ephe_service):
    dt = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)
    jd = ephe_service.datetime_to_julian_day(dt)
    houses = ephe_service.calculate_houses(
        jd=jd,
        latitude=22.5726,
        longitude=88.3639,
        house_system=HouseSystem.PLACIDUS,
    )

    assert len(houses.cusps) == 12
    assert 0.0 <= houses.ascendant < 360.0
    assert 0.0 <= houses.midheaven < 360.0


def test_golden_charts_verification(astro_engine):
    for _chart_key, golden in GOLDEN_CHARTS.items():
        sys_enum = AstrologySystem.VEDIC if golden.system == "vedic" else AstrologySystem.WESTERN
        chart = astro_engine.calculate_natal(
            utc_datetime=golden.utc_datetime,
            latitude=golden.latitude,
            longitude=golden.longitude,
            system=sys_enum,
        )

        assert "planets" in chart
        assert "houses" in chart

        # Verify Sun
        sun = chart["planets"]["Sun"]
        assert (
            abs(sun["longitude"] - golden.expected_sun.approx_lon) <= golden.expected_sun.tolerance
            or abs((sun["longitude"] - golden.expected_sun.approx_lon + 360) % 360)
            <= golden.expected_sun.tolerance
        )

        # Verify Moon
        moon = chart["planets"]["Moon"]
        assert (
            abs(moon["longitude"] - golden.expected_moon.approx_lon)
            <= golden.expected_moon.tolerance
            or abs((moon["longitude"] - golden.expected_moon.approx_lon + 360) % 360)
            <= golden.expected_moon.tolerance
        )
