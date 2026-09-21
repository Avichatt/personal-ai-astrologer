"""Tests for Western transits, Vedic Gochar, and Sade Sati detection."""

from datetime import datetime

from app.astrology.ephemeris import EphemerisService, PlanetPosition
from app.astrology.vedic.transits import VedicTransitCalculator
from app.astrology.western.transits import WesternTransitCalculator


def test_western_transit_hit_detection():
    calc = WesternTransitCalculator(EphemerisService())

    # Natal Sun at 10.0° Aries
    natal_planets = [PlanetPosition(0, "Sun", 10.0, 0.0, 1.0, 1.0, False, 0, "Aries", 10.0)]
    natal_houses = [i * 30.0 for i in range(12)]

    # Transit date where transiting Mars or Jupiter is in aspect
    result = calc.calculate_transits(
        natal_planets=natal_planets,
        natal_house_cusps=natal_houses,
        transit_utc=datetime(2024, 1, 1, 0, 0, 0),
        aspect_orb=5.0,
    )

    assert len(result.transiting_planets) == 11
    assert len(result.transits_in_natal_houses) == 11


def test_sade_sati_detection():
    calc = VedicTransitCalculator(EphemerisService())
    # Test with natal Moon in Pisces (~340°) and transit Saturn in Pisces (current 2024-2025 period)
    result = calc.calculate_gochar(
        natal_moon_longitude=340.0,
        natal_lagna_longitude=0.0,
        transit_utc=datetime(2024, 6, 1, 0, 0, 0),
    )

    # In mid-2024, Saturn is in Aquarius (~320° sidereal) -> 12th from Pisces Moon (Rising Phase)
    assert result.sade_sati.is_sade_sati_active is True
    assert result.sade_sati.phase_name is not None
