"""Tests for AstroEventDetector and EventRanker significance scoring."""

from datetime import datetime

from app.astro_events.detector import AstroEventDetector
from app.astro_events.significance import EventRanker, EventSignificanceTier
from app.config.constants import AspectType, AstroEventType


def test_event_significance_ranking():
    # Eclipse should rank as PINNACLE
    eclipse_score = EventRanker.rank_event(
        event_type=AstroEventType.ECLIPSE,
        primary_body="Moon",
        secondary_body="Sun",
        is_exact=True,
    )
    assert eclipse_score.tier == EventSignificanceTier.PINNACLE
    assert eclipse_score.score >= 85.0

    # Fast minor transit should rank lower
    fast_score = EventRanker.rank_event(
        event_type=AstroEventType.MAJOR_ASPECT,
        primary_body="Mercury",
        secondary_body="Venus",
        aspect_type=AspectType.SEXTILE,
    )
    assert fast_score.score < 80.0


def test_mundane_event_detection():
    detector = AstroEventDetector()
    events = detector.detect_mundane_events(
        start_utc=datetime(2024, 1, 1, 0, 0, 0),
        days=60,
    )
    assert len(events) >= 1
    # Check that events have titles, scores, and tiers
    assert events[0].title != ""
    assert events[0].score > 0
