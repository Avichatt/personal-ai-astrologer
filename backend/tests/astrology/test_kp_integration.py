"""Integration tests for KP Astrology engine, facade, and AI interpretation service."""

from datetime import UTC, datetime
import pytest

from app.astrology.engine import AstrologyEngine
from app.config.constants import AstrologySystem, Ayanamsa, HouseSystem
from app.schemas.analysis import AnalysisFocus, HoroscopeAnalysisResponse
from app.services.ai_interpretation import AstroInterpretationService


class TestKpIntegration:
    """Test full integration of KP system across engine, interpretation, and life blueprint."""

    def setup_method(self) -> None:
        self.engine = AstrologyEngine()
        self.interpreter = AstroInterpretationService()
        self.test_dt = datetime(1992, 7, 18, 9, 15, 0, tzinfo=UTC)
        self.lat = 12.9716
        self.lon = 77.5946  # Bengaluru

    def test_engine_calculate_natal_kp(self) -> None:
        """AstrologyEngine.calculate_natal supports AstrologySystem.KP seamlessly."""
        chart_dict = self.engine.calculate_natal(
            utc_datetime=self.test_dt,
            latitude=self.lat,
            longitude=self.lon,
            system=AstrologySystem.KP,
        )

        assert chart_dict["system"] == "kp"
        assert "cuspal_analysis" in chart_dict
        assert len(chart_dict["cuspal_analysis"]) == 12
        assert "significators" in chart_dict
        assert "ruling_planets_at_birth" in chart_dict

    def test_kp_career_interpretation(self) -> None:
        """AstroInterpretationService produces structured KP career reading."""
        chart_dict = self.engine.calculate_natal(
            utc_datetime=self.test_dt,
            latitude=self.lat,
            longitude=self.lon,
            system=AstrologySystem.KP,
        )

        response = self.interpreter.generate_analysis(
            chart_dict=chart_dict,
            focus=AnalysisFocus.CAREER,
            target_date=datetime(2026, 9, 21, tzinfo=UTC),
            name="Siddharth",
            system=AstrologySystem.KP,
        )

        assert isinstance(response, HoroscopeAnalysisResponse)
        assert response.system == "kp"
        assert response.name == "Siddharth"
        assert len(response.sections) >= 3
        assert len(response.timeline) >= 2

        # Check KP rule and sub-lord contents
        raw_text = response.formatted_reading
        assert "KP" in raw_text or "Krishnamurti" in raw_text
        assert "Sub-Lord" in raw_text
        assert "10th Cusp" in raw_text

    def test_kp_life_blueprint_interpretation(self) -> None:
        """AstroInterpretationService produces 7-section KP Life Blueprint."""
        chart_dict = self.engine.calculate_natal(
            utc_datetime=self.test_dt,
            latitude=self.lat,
            longitude=self.lon,
            system=AstrologySystem.KP,
        )

        response = self.interpreter.generate_analysis(
            chart_dict=chart_dict,
            focus=AnalysisFocus.LIFE_BLUEPRINT,
            target_date=datetime(2026, 9, 21, tzinfo=UTC),
            name="Siddharth",
            system=AstrologySystem.KP,
        )

        assert isinstance(response, HoroscopeAnalysisResponse)
        assert response.system == "kp"
        assert len(response.life_stages) == 5
        assert len(response.gemstone_recommendations) >= 2
        assert len(response.spiritual_remedies) >= 3

        raw_text = response.formatted_reading
        assert "KP (Krishnamurti Paddhati)" in raw_text or "KP System" in raw_text
        assert "Whole-Life Journey" in raw_text
        assert "Gemstone Prescription" in raw_text

    def test_multi_system_selection(self) -> None:
        """Ensure users can select Vedic, Western, or KP and receive accurate systems."""
        # 1. Vedic
        vedic_chart = self.engine.calculate_natal(
            utc_datetime=self.test_dt,
            latitude=self.lat,
            longitude=self.lon,
            system=AstrologySystem.VEDIC,
        )
        assert vedic_chart["system"] == "vedic"

        # 2. KP
        kp_chart = self.engine.calculate_natal(
            utc_datetime=self.test_dt,
            latitude=self.lat,
            longitude=self.lon,
            system=AstrologySystem.KP,
        )
        assert kp_chart["system"] == "kp"

        # 3. Western
        western_chart = self.engine.calculate_natal(
            utc_datetime=self.test_dt,
            latitude=self.lat,
            longitude=self.lon,
            system=AstrologySystem.WESTERN,
        )
        assert western_chart["system"] == "western"
