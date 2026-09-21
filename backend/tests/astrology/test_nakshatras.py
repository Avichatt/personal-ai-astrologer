"""Tests for 27 Nakshatras and 108 Padas calculations."""

from app.astrology.vedic.nakshatras import Gana, NakshatraCalculator


def test_nakshatra_ashwini():
    # 0°00' Aries -> Ashwini Pada 1
    info = NakshatraCalculator.calculate_from_longitude(0.0)
    assert info.name == "Ashwini"
    assert info.pada == 1
    assert info.ruler == "Ketu"
    assert info.gana == Gana.DEVA
    assert info.navamsha_sign_name == "Mesha"  # Pada 1 of Ashwini = Aries in D9


def test_nakshatra_rohini():
    # 40°00' = Taurus 10° -> Rohini (spans 40° to 53°20')
    info = NakshatraCalculator.calculate_from_longitude(45.0)
    assert info.name == "Rohini"
    assert info.ruler == "Moon"
    assert info.deity.startswith("Brahma")
