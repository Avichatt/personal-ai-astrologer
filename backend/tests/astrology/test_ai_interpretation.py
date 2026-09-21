"""Tests for AI Horoscope Interpretation Service and structured readings."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from app.astrology.engine import get_astrology_engine
from app.config.constants import AstrologySystem
from app.schemas.analysis import AnalysisFocus
from app.services.ai_interpretation import AstroInterpretationService


@pytest.fixture
def sample_chart():
    engine = get_astrology_engine()
    # Kolkata 1995 golden chart
    birth_utc = datetime(1995, 5, 10, 9, 5, tzinfo=UTC)
    return engine.calculate_natal(
        utc_datetime=birth_utc,
        latitude=22.5726,
        longitude=88.3639,
        system=AstrologySystem.VEDIC,
    )


def test_career_analysis_structure(sample_chart):
    service = AstroInterpretationService()
    target_dt = datetime(2026, 8, 1, tzinfo=UTC)

    result = service.generate_analysis(
        chart_dict=sample_chart,
        focus=AnalysisFocus.CAREER,
        target_date=target_dt,
        name="Arjun",
        system=AstrologySystem.VEDIC,
    )

    # Validate output structure
    assert result.name == "Arjun"
    assert result.focus == "career"
    assert result.system == "vedic"
    assert result.ascendant in ("Kanya", "Simha", "Mesha", "Tula")  # valid Vedic rashi
    assert len(result.sections) >= 3
    assert len(result.timeline) >= 2

    # Check that formatted reading contains the exact formatting elements from the user's template
    text = result.formatted_reading
    assert "◆ 10th House (Career House) Analysis" in text
    assert "Parashari rule:" in text
    assert "10th lord +" in text
    assert "✦ Career promise is STRONG." in text
    assert "◆ Why Delay Happening?" in text
    assert "8th house involvement" in text
    assert "✓ Sudden breaks" in text
    assert "✓ Frustration" in text
    assert "Not destruction, karmic restructuring" in text
    assert "◆ Current Mahadasha–Antardasha (2026 context)" in text
    assert "◆ Exact Career Rise Timeline (Parashari Dasha Based)" in text
    assert "✦" in text
    assert "First Opportunity" in text


def test_love_and_finance_focus_domains(sample_chart):
    service = AstroInterpretationService()
    target_dt = datetime(2026, 6, 1, tzinfo=UTC)

    # Love
    love_res = service.generate_analysis(
        chart_dict=sample_chart,
        focus=AnalysisFocus.LOVE,
        target_date=target_dt,
    )
    assert "7th House" in love_res.formatted_reading
    assert "Parashari rule:" in love_res.formatted_reading
    assert len(love_res.timeline) >= 2

    # Finance
    fin_res = service.generate_analysis(
        chart_dict=sample_chart,
        focus=AnalysisFocus.FINANCE,
        target_date=target_dt,
    )
    assert "2nd & 11th Houses" in fin_res.formatted_reading
    assert "Dhana Yoga" in fin_res.formatted_reading
    assert len(fin_res.timeline) >= 2


def test_gemini_integration_parsing(sample_chart):
    """Test that if Gemini returns formatted text, the parser extracts sections and timeline correctly."""
    service = AstroInterpretationService()
    mock_text = """
--------------------------------------------------
◆ 10th House (Career House) Analysis
10th house lord connected with:
• 6th house (service/job)
• 11th house (income)
• Saturn/Mercury influence

Parashari rule:
10th lord + 6th connection = service/job assured.
10th lord + 11th = income confirmed.

✦ Career promise is STRONG.
No denial. Only delay.

--------------------------------------------------
◆ Why Delay Happening?
8th house involvement + Saturn transit effect |

8th influence gives:
✓ Sudden breaks
✓ Frustration
✓ Direction confusion
✓ Confidence drop

Not destruction, karmic restructuring |

--------------------------------------------------
◆ Current Mahadasha–Antardasha (2026 context)
Running dasha activating:
• Saturn type energy
• 8th house themes
• Transformation period

Saturn dasha first half tough.
Second half stability.

In your case: 2026 mid stagnation | 2026 end movement

--------------------------------------------------
◆ Exact Career Rise Timeline (Parashari Dasha Based)
✦ August 2026 – First Opportunity
Interview / contract / joining probability |

✦ January 2027 – Strong Activation
Stable job likely |

✦ 2028 – Growth Phase
Role clarity + income stabilization |
--------------------------------------------------
"""
    with patch.object(service, "_generate_with_gemini", return_value=mock_text):
        with patch.object(service.settings, "gemini_api_key", "test-key"):
            res = service.generate_analysis(
                chart_dict=sample_chart,
                focus=AnalysisFocus.CAREER,
                target_date=datetime(2026, 8, 1, tzinfo=UTC),
            )
            assert len(res.sections) == 4
            assert len(res.timeline) == 3
            assert res.timeline[0].timeframe == "August 2026"
            assert res.timeline[0].phase == "First Opportunity"
            assert "Interview / contract / joining probability" in res.timeline[0].prediction
            assert res.timeline[1].timeframe == "January 2027"
            assert res.timeline[1].phase == "Strong Activation"
