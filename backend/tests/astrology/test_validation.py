"""Tests for chart validation rules and invariants."""

import pytest

from app.astrology.ephemeris import HousePositions, PlanetPosition
from app.astrology.validation import ChartValidationError, ChartValidator


def test_validator_valid_planet():
    pos = PlanetPosition(
        planet_id=0,
        name="Sun",
        longitude=125.45,
        latitude=0.0,
        distance=1.01,
        speed_longitude=0.98,
        is_retrograde=False,
        sign_index=4,
        sign_name="Leo",
        sign_longitude=5.45,
    )
    ChartValidator.validate_planet_position(pos)


def test_validator_invalid_longitude():
    pos = PlanetPosition(
        planet_id=0,
        name="Sun",
        longitude=365.0,  # Invalid
        latitude=0.0,
        distance=1.01,
        speed_longitude=0.98,
        is_retrograde=False,
        sign_index=0,
        sign_name="Aries",
        sign_longitude=5.0,
    )
    with pytest.raises(ChartValidationError):
        ChartValidator.validate_planet_position(pos)


def test_validator_invalid_sign_index():
    pos = PlanetPosition(
        planet_id=0,
        name="Sun",
        longitude=50.0,
        latitude=0.0,
        distance=1.0,
        speed_longitude=1.0,
        is_retrograde=False,
        sign_index=15,  # Invalid
        sign_name="Unknown",
        sign_longitude=20.0,
    )
    with pytest.raises(ChartValidationError):
        ChartValidator.validate_planet_position(pos)


def test_validator_invalid_house_count():
    houses = HousePositions(
        system="placidus",
        cusps=[10.0, 40.0, 70.0],  # Only 3 cusps
        ascendant=10.0,
        midheaven=280.0,
        armc=280.0,
        vertex=190.0,
    )
    with pytest.raises(ChartValidationError):
        ChartValidator.validate_house_positions(houses)
