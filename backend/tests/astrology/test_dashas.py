"""Tests for Vimshottari Dasha calculations (Mahadasha, Antardasha, and Active lookup)."""

from datetime import datetime

import pytest

from app.astrology.vedic.antardasha import DashaTreeBuilder
from app.astrology.vedic.dashas import VimshottariDashaEngine


def test_vimshottari_mahadasha_balance_and_order():
    # Moon at 0° Aries = Ashwini nakshatra (Ruler: Ketu)
    # Elapsed fraction = 0.0 -> full 7 years of Ketu
    birth_dt = datetime(2000, 1, 1, 0, 0, 0)
    dashas = VimshottariDashaEngine.calculate_mahadashas(
        moon_sidereal_longitude=0.0,
        birth_datetime_utc=birth_dt,
    )

    assert dashas[0].lord == "Ketu"
    assert pytest.approx(dashas[0].duration_years, abs=0.1) == 7.0
    assert dashas[1].lord == "Venus"
    assert pytest.approx(dashas[1].duration_years, abs=0.1) == 20.0
    assert dashas[2].lord == "Sun"
    assert pytest.approx(dashas[2].duration_years, abs=0.1) == 6.0
    assert dashas[3].lord == "Moon"
    assert pytest.approx(dashas[3].duration_years, abs=0.1) == 10.0


def test_active_dasha_lookup():
    birth_dt = datetime(2000, 1, 1, 0, 0, 0)
    # Moon at 0° Aries (Starts in Ketu Mahadasha)
    # 2 years after birth (2002-01-01) -> Still in Ketu Mahadasha
    active_2002 = DashaTreeBuilder.find_active_dasha(
        moon_sidereal_lon=0.0,
        birth_utc=birth_dt,
        target_utc=datetime(2002, 1, 1, 0, 0, 0),
    )
    assert active_2002.mahadasha == "Ketu"

    # 10 years after birth (2010-01-01) -> Ketu (7 yrs) finished, in Venus Mahadasha
    active_2010 = DashaTreeBuilder.find_active_dasha(
        moon_sidereal_lon=0.0,
        birth_utc=birth_dt,
        target_utc=datetime(2010, 1, 1, 0, 0, 0),
    )
    assert active_2010.mahadasha == "Venus"
