"""Tests for Complete Professional Horoscope Analysis (Birth to Death Life Blueprint)."""

from datetime import UTC, datetime
import pytest

from app.astrology.engine import get_astrology_engine
from app.config.constants import AstrologySystem
from app.schemas.analysis import AnalysisFocus
from app.services.ai_interpretation import AstroInterpretationService


@pytest.fixture
def sample_chart():
    engine = get_astrology_engine()
    # Kolkata 1995 golden chart (Sun=Mesha, Moon=Kanya, Lagna=Kanya)
    birth_utc = datetime(1995, 5, 10, 9, 5, tzinfo=UTC)
    return engine.calculate_natal(
        utc_datetime=birth_utc,
        latitude=22.5726,
        longitude=88.3639,
        system=AstrologySystem.VEDIC,
    )


def test_complete_life_blueprint_structure(sample_chart):
    service = AstroInterpretationService()
    target_dt = datetime(2026, 8, 1, tzinfo=UTC)

    result = service.generate_analysis(
        chart_dict=sample_chart,
        focus=AnalysisFocus.LIFE_BLUEPRINT,
        target_date=target_dt,
        name="Arjun Mukherjee",
        system=AstrologySystem.VEDIC,
    )

    # 1. High level response fields
    assert result.name == "Arjun Mukherjee"
    assert result.focus == "life_blueprint"
    assert result.system == "vedic"

    # 2. Seven Core Sections Verification
    text = result.formatted_reading
    assert "◆ Birth Chart Foundation & Technical Matrix" in text
    assert "◆ Classical Yogas & Planetary Strengths" in text
    assert "◆ Divisional Charts (Varga Insights)" in text
    assert "◆ Whole-Life Journey: Birth to Death (5 Chronological Stages)" in text
    assert "◆ Strategic Life Decisions & Action Plan" in text
    assert "◆ Gemstone Prescription (Ratna Chikitsa)" in text
    assert "◆ Spiritual & Practical Remedies (Upayas)" in text

    # 3. Formatted aesthetic indicators
    assert "Parashari rule:" in text
    assert "•" in text
    assert "✓" in text
    assert "✦" in text
    assert "--------------------------------------------------" in text

    # 4. Five Life Stages (Birth to Death)
    assert len(result.life_stages) == 5
    stage_brackets = [s.age_bracket for s in result.life_stages]
    assert "0–18 Years" in stage_brackets
    assert "18–30 Years" in stage_brackets
    assert "30–50 Years" in stage_brackets
    assert "50–65 Years" in stage_brackets
    assert "65+ Years" in stage_brackets

    for st in result.life_stages:
        assert len(st.key_themes) >= 2
        assert len(st.milestones) >= 1
        assert len(st.guidance) > 10
        assert "Mahadasha" in st.dasha_context or "planetary" in st.dasha_context

    # 5. Gemstone Prescriptions
    assert len(result.gemstone_recommendations) >= 3
    categories = [g.category for g in result.gemstone_recommendations]
    assert any("Life Stone" in c for c in categories)
    assert any("Lucky Stone" in c for c in categories)
    assert any("Contraindicated" in c for c in categories)

    for g in result.gemstone_recommendations:
        if not g.is_contraindicated:
            assert g.metal != "None"
            assert g.finger != "DO NOT WEAR"
            assert "Om" in g.consecration_mantra
        else:
            assert g.is_contraindicated is True
            assert "NEVER WEAR" in text or "Contraindications" in text

    # 6. Spiritual & Practical Remedies
    assert len(result.spiritual_remedies) >= 4
    rem_categories = [r.category for r in result.spiritual_remedies]
    assert "Beej Mantra" in rem_categories
    assert "Stotra" in rem_categories
    assert "Charity (Daan)" in rem_categories
    assert "Fasting (Vrat)" in rem_categories
