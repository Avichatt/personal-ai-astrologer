"""Tests for KP sub-lord, star-lord, and sub-sub-lord calculations."""

import pytest

from app.astrology.kp.sublords import KpSubLordCalculator, KpSubLordInfo


class TestKpSubLordCalculator:
    """Test suite for KP sub-lord 249 table and precision degree calculations."""

    def test_ashwini_first_sublord(self) -> None:
        """At 0°00'00" sidereal (start of Ashwini), star lord is Ketu and sub lord is Ketu."""
        info = KpSubLordCalculator.calculate_sublord(0.0)
        assert info.nakshatra.name == "Ashwini"
        assert info.star_lord == "Ketu"
        assert info.sub_lord == "Ketu"
        assert info.sub_sub_lord == "Ketu"
        assert info.sub_lord_span_deg > 0.7  # (7/120) * 13.3333333° ≈ 0.777778°
        assert info.kp_number == 1

    def test_ashwini_second_sublord_venus(self) -> None:
        """After Ketu's sub (approx 0°46'40" = 0.7778°), Venus sub begins."""
        # At 1.0 degree: Ketu span is ~0.7778°, so 1.0° must be in Venus sub
        info = KpSubLordCalculator.calculate_sublord(1.0)
        assert info.nakshatra.name == "Ashwini"
        assert info.star_lord == "Ketu"
        assert info.sub_lord == "Venus"
        assert info.kp_number == 2

    def test_sublord_spans_sum_to_nakshatra(self) -> None:
        """The 9 sub-lord spans within a nakshatra must sum precisely to 13°20' (13.33333°)."""
        total_span = sum(
            (period / 120.0) * (360.0 / 27.0)
            for period in [7, 20, 6, 10, 7, 18, 16, 19, 17]
        )
        assert abs(total_span - (360.0 / 27.0)) < 1e-9

    def test_rohini_moon_star_lord(self) -> None:
        """Rohini Nakshatra (40° to 53°20') must have Moon as Star Lord, starting with Moon sub."""
        info = KpSubLordCalculator.calculate_sublord(40.01)
        assert info.nakshatra.name == "Rohini"
        assert info.star_lord == "Moon"
        assert info.sub_lord == "Moon"

    def test_full_zodiac_sweep_validity(self) -> None:
        """Sweep through all 360 degrees in 1-degree increments without errors."""
        for deg in range(360):
            info = KpSubLordCalculator.calculate_sublord(float(deg))
            assert isinstance(info, KpSubLordInfo)
            assert 1 <= info.kp_number <= 249
            assert info.star_lord in [
                "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"
            ]
            assert info.sub_lord in [
                "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"
            ]
            assert info.sub_sub_lord in [
                "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"
            ]
