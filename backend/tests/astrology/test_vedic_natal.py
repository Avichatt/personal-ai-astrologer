"""Tests for Vedic Natal Chart (Kundli) calculation, Graha dignities, and Jaimini Karakas."""

from datetime import datetime

from app.astrology.ephemeris import EphemerisService
from app.astrology.vedic.natal import VedicNatalChartEngine
from app.config.constants import Ayanamsa


def test_vedic_natal_chart_kolkata_golden():
    engine = VedicNatalChartEngine(EphemerisService())
    # Kolkata, India: 1995-05-10 09:05:00 UTC (14:35 IST)
    dt_utc = datetime(1995, 5, 10, 9, 5, 0)
    lat, lng = 22.5726, 88.3639

    chart = engine.calculate_chart(
        dt_utc=dt_utc,
        latitude=lat,
        longitude=lng,
        ayanamsa=Ayanamsa.LAHIRI,
    )

    assert chart.system == "vedic"
    assert chart.ayanamsa == "lahiri"
    assert chart.ayanamsa_value > 23.0
    assert (
        chart.ascendant_rashi == "Kanya"
    )  # Kanya (Virgo) Ascendant in Lahiri for 14:35 IST Kolkata
    assert len(chart.grahas) == 9  # Sun..Saturn + Rahu + Ketu
    assert len(chart.bhavas) == 12
    assert len(chart.karakas) == 8  # 8 Jaimini Chara Karakas (AK .. DK)

    # Verify Atmakaraka (AK) is present
    ak = next(k for k in chart.karakas if k.code == "AK")
    assert ak.title.startswith("Atmakaraka")
    assert ak.planet_name != ""

    # Verify D1 and D9 charts generated
    assert chart.d1_rashi_chart.division_number == 1
    assert chart.d9_navamsha_chart.division_number == 9
    assert len(chart.mahadashas) >= 9
