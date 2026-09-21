"""Tests for Western Natal Chart calculation, houses, and elemental synthesis."""

from datetime import datetime

from app.astrology.ephemeris import EphemerisService
from app.astrology.western.natal import WesternNatalChartEngine
from app.config.constants import HouseSystem


def test_western_natal_chart_generation():
    engine = WesternNatalChartEngine(EphemerisService())
    # Kolkata, India test: 1995-05-10 09:05:00 UTC (14:35 IST)
    dt_utc = datetime(1995, 5, 10, 9, 5, 0)
    lat, lng = 22.5726, 88.3639

    chart = engine.calculate_chart(
        dt_utc=dt_utc,
        latitude=lat,
        longitude=lng,
        house_system=HouseSystem.PLACIDUS,
    )

    assert chart.system == "western"
    assert chart.house_system == "placidus"
    assert chart.sun_sign == "Taurus"
    assert chart.moon_sign == "Virgo"
    assert chart.ascendant_sign == "Libra"
    assert len(chart.planets) == 11
    assert len(chart.houses) == 12

    # Verify house structure
    h1 = chart.houses[0]
    assert h1.house_number == 1
    assert h1.sign_name == "Libra"

    # Verify elemental balance
    assert chart.balance.earth >= 2
    assert chart.chart_signature != ""
    assert "ascendant" in chart.angles
    assert "midheaven" in chart.angles
