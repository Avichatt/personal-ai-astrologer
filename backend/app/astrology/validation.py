"""Validation rules and integrity checks for astronomical and astrological chart outputs."""

from __future__ import annotations

from app.astrology.ephemeris import HousePositions, PlanetPosition


class ChartValidationError(ValueError):
    """Raised when an astrological chart calculation output violates physical or geometric invariants."""

    pass


class ChartValidator:
    """Validates planetary positions, house cusps, and astrological metrics."""

    @staticmethod
    def validate_planet_position(pos: PlanetPosition) -> None:
        """Validate a single planet position."""
        if not (0.0 <= pos.longitude < 360.0):
            raise ChartValidationError(
                f"Planet {pos.name} has invalid longitude {pos.longitude} (expected 0 <= lon < 360)"
            )
        if not (-90.0 <= pos.latitude <= 90.0):
            raise ChartValidationError(
                f"Planet {pos.name} has invalid latitude {pos.latitude} (expected -90 <= lat <= 90)"
            )
        if not (0 <= pos.sign_index <= 11):
            raise ChartValidationError(
                f"Planet {pos.name} has invalid sign_index {pos.sign_index} (expected 0 <= idx <= 11)"
            )
        if not (0.0 <= pos.sign_longitude < 30.000001):
            raise ChartValidationError(
                f"Planet {pos.name} has invalid sign_longitude {pos.sign_longitude} (expected 0 <= deg < 30)"
            )
        if pos.distance < 0.0:
            raise ChartValidationError(f"Planet {pos.name} has negative distance {pos.distance}")

    @staticmethod
    def validate_house_positions(houses: HousePositions) -> None:
        """Validate house cusps and cardinal angles."""
        if len(houses.cusps) != 12:
            raise ChartValidationError(f"Expected exactly 12 house cusps, got {len(houses.cusps)}")
        for i, cusp in enumerate(houses.cusps, start=1):
            if not (0.0 <= cusp < 360.0):
                raise ChartValidationError(
                    f"House cusp {i} has invalid longitude {cusp} (expected 0 <= cusp < 360)"
                )
        if not (0.0 <= houses.ascendant < 360.0):
            raise ChartValidationError(
                f"Ascendant has invalid longitude {houses.ascendant} (expected 0 <= asc < 360)"
            )
        if not (0.0 <= houses.midheaven < 360.0):
            raise ChartValidationError(
                f"Midheaven has invalid longitude {houses.midheaven} (expected 0 <= mc < 360)"
            )

    @classmethod
    def validate_chart_data(
        cls,
        planets: dict[str, PlanetPosition],
        houses: HousePositions,
    ) -> None:
        """Validate full set of planetary positions and house cusps."""
        for planet in planets.values():
            cls.validate_planet_position(planet)
        cls.validate_house_positions(houses)
