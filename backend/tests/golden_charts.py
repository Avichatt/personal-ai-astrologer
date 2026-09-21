"""Golden reference chart dataset for calculation engine verification."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class ExpectedPlanetPosition:
    name: str
    sign: str
    approx_lon: float  # Expected longitude in degrees
    tolerance: float = 3.0  # Allowed tolerance for test verification (deg)


@dataclass(frozen=True)
class GoldenChart:
    name: str
    description: str
    utc_datetime: datetime
    latitude: float
    longitude: float
    system: str
    expected_sun: ExpectedPlanetPosition
    expected_moon: ExpectedPlanetPosition
    expected_ascendant_sign: str


GOLDEN_CHARTS: dict[str, GoldenChart] = {
    "kolkata_1995": GoldenChart(
        name="Kolkata Vedic Chart",
        description="Kolkata, India — 1995-05-10 14:35 IST",
        utc_datetime=datetime(1995, 5, 10, 9, 5, 0, tzinfo=UTC),
        latitude=22.5726,
        longitude=88.3639,
        system="vedic",
        expected_sun=ExpectedPlanetPosition(
            name="Sun",
            sign="Mesha",
            approx_lon=25.5,
            tolerance=4.0,
        ),
        expected_moon=ExpectedPlanetPosition(
            name="Moon",
            sign="Kanya",
            approx_lon=152.6,
            tolerance=4.0,
        ),
        expected_ascendant_sign="Simha",
    ),
    "new_york_1990": GoldenChart(
        name="New York Western Chart",
        description="New York, USA — 1990-01-15 08:30 EST",
        utc_datetime=datetime(1990, 1, 15, 13, 30, 0, tzinfo=UTC),
        latitude=40.7128,
        longitude=-74.0060,
        system="western",
        expected_sun=ExpectedPlanetPosition(
            name="Sun",
            sign="Capricorn",
            approx_lon=295.0,
            tolerance=3.0,
        ),
        expected_moon=ExpectedPlanetPosition(
            name="Moon",
            sign="Virgo",
            approx_lon=163.4,
            tolerance=4.0,
        ),
        expected_ascendant_sign="Aquarius",
    ),
    "london_1985": GoldenChart(
        name="London Western Chart",
        description="London, UK — 1985-07-20 22:15 BST",
        utc_datetime=datetime(1985, 7, 20, 21, 15, 0, tzinfo=UTC),
        latitude=51.5074,
        longitude=-0.1278,
        system="western",
        expected_sun=ExpectedPlanetPosition(
            name="Sun",
            sign="Cancer",
            approx_lon=118.0,
            tolerance=3.0,
        ),
        expected_moon=ExpectedPlanetPosition(
            name="Moon",
            sign="Virgo",
            approx_lon=155.0,
            tolerance=5.0,
        ),
        expected_ascendant_sign="Pisces",
    ),
}
