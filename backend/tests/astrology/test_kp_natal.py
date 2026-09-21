"""Tests for KP Natal Chart Engine calculation and serialization."""

from datetime import UTC, datetime
import pytest

from app.astrology.ephemeris import EphemerisService
from app.astrology.kp.natal import KpGrahaInfo, KpNatalChartEngine, KpNatalChartResult, KpRulingPlanets
from app.config.constants import Ayanamsa, HouseSystem


class TestKpNatalChartEngine:
    """Test suite for KP Natal Chart calculation engine."""

    def test_calculate_kp_chart_complete(self) -> None:
        """Calculate complete KP natal chart for a realistic birth timestamp."""
        ephem = EphemerisService()
        engine = KpNatalChartEngine(ephem)

        dt_utc = datetime(1988, 10, 24, 14, 30, 0, tzinfo=UTC)
        query_dt = datetime(2026, 9, 21, 10, 0, 0, tzinfo=UTC)
        lat, lon = 28.6139, 77.2090  # New Delhi

        result = engine.calculate_chart(
            dt_utc=dt_utc,
            latitude=lat,
            longitude=lon,
            ayanamsa=Ayanamsa.KRISHNAMURTI,
            query_dt_utc=query_dt,
        )

        assert isinstance(result, KpNatalChartResult)
        assert result.system == "kp"
        assert result.ayanamsa == Ayanamsa.KRISHNAMURTI.value

        # Ascendant checks
        assert 0.0 <= result.ascendant_longitude < 360.0
        assert result.ascendant_sublord_info is not None
        assert result.ascendant_sublord_info.star_lord in [
            "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"
        ]
        assert result.ascendant_sublord_info.sub_lord in [
            "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"
        ]

        # Grahas
        assert len(result.grahas) >= 9
        for g in result.grahas:
            assert isinstance(g, KpGrahaInfo)
            assert g.star_lord != ""
            assert g.sub_lord != ""
            assert 1 <= g.kp_number <= 249
            assert 1 <= g.house_number <= 12

        # Placidus cuspal analysis
        assert len(result.cuspal_analysis) == 12
        for cusp in result.cuspal_analysis:
            assert 1 <= cusp.cusp_number <= 12
            assert cusp.sign_lord != ""
            assert cusp.star_lord != ""
            assert cusp.sub_lord != ""

        # Significators
        assert len(result.significators) >= 7

        # Ruling planets
        assert isinstance(result.ruling_planets_at_birth, KpRulingPlanets)
        assert result.ruling_planets_at_birth.ascendant_sign_lord != ""
        assert result.ruling_planets_at_birth.moon_star_lord != ""
        assert result.ruling_planets_at_birth.day_lord != ""

        assert result.ruling_planets_at_query is not None
        assert result.ruling_planets_at_query.day_lord != ""

        # Dashas
        assert len(result.mahadashas) == 9
        assert result.active_dasha_at_birth is not None

        # Serialization to dict
        chart_dict = result.to_dict()
        assert chart_dict["system"] == "kp"
        assert "cuspal_analysis" in chart_dict
        assert "significators" in chart_dict
        assert "ruling_planets_at_birth" in chart_dict
        assert len(chart_dict["grahas"]) >= 9
