"""Tests for Divisional Charts (Vargas D1 to D60)."""

from app.astrology.ephemeris import PlanetPosition
from app.astrology.vedic.divisional_charts import DivisionalChartEngine


def test_d9_navamsha_mapping():
    # Fire signs (Aries: 0°-30°) Navamsha 1 (0°-3°20') is Aries, Navamsha 2 (3°20'-6°40') is Taurus
    sign_idx, deg = DivisionalChartEngine.calculate_d9_navamsha(1.0)
    assert sign_idx == 0  # Aries

    sign_idx, deg = DivisionalChartEngine.calculate_d9_navamsha(4.0)
    assert sign_idx == 1  # Taurus


def test_varga_chart_generation():
    planets = [
        PlanetPosition(0, "Sun", 15.0, 0.0, 1.0, 1.0, False, 0, "Aries", 15.0),
        PlanetPosition(1, "Moon", 45.0, 0.0, 0.002, 13.0, False, 1, "Taurus", 15.0),
    ]

    d10 = DivisionalChartEngine.generate_divisional_chart(
        division=10,
        ascendant_lon=0.0,
        planets=planets,
    )

    assert d10.division_number == 10
    assert d10.name == "D10 Dashamsha"
    assert len(d10.placements) == 2
