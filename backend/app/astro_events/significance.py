"""Event significance evaluation and ranking engine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.config.constants import AspectType, AstroEventType


class EventSignificanceTier(StrEnum):
    PINNACLE = "pinnacle"  # 85-100: Eclipses, Saturn/Pluto outer stations, major personal transits
    HIGH = "high"  # 70-84: Ingresses of slow planets, Jupiter/Saturn aspects, New/Full Moons
    MODERATE = "moderate"  # 45-69: Personal planet stations, Mars transits, major lunations
    MILD = "mild"  # 20-44: Mercury/Venus quick aspects, minor lunar phases
    BACKGROUND = "background"  # 0-19: Fast fleeting moon transits


@dataclass(frozen=True)
class EventScore:
    """Calculated importance score and classification."""

    score: float  # 0.0 to 100.0
    tier: EventSignificanceTier
    rationale: str


class EventRanker:
    """Calculates weighted importance scores for mundane and personalized astro events."""

    BASE_SCORES: dict[AstroEventType, float] = {
        AstroEventType.ECLIPSE: 92.0,
        AstroEventType.RETROGRADE_START: 75.0,
        AstroEventType.RETROGRADE_END: 75.0,
        AstroEventType.STATIONARY: 80.0,
        AstroEventType.PLANETARY_INGRESS: 65.0,
        AstroEventType.LUNAR_PHASE: 60.0,
        AstroEventType.MAJOR_ASPECT: 55.0,
        AstroEventType.TRANSIT_TO_NATAL: 70.0,
        AstroEventType.DASHA_CHANGE: 88.0,
    }

    OUTER_PLANETS = {
        "Saturn",
        "Jupiter",
        "Uranus",
        "Neptune",
        "Pluto",
        "North Node",
        "Rahu",
        "Ketu",
    }
    LUMINARIES = {"Sun", "Moon"}
    ANGLES = {"Ascendant", "Midheaven", "Descendant", "Imum Coeli"}

    @classmethod
    def rank_event(
        cls,
        event_type: AstroEventType,
        primary_body: str,
        secondary_body: str | None = None,
        aspect_type: AspectType | None = None,
        is_exact: bool = False,
        orb: float = 0.0,
    ) -> EventScore:
        """
        Evaluate multi-factor astrological significance score (0 to 100).
        """
        base = cls.BASE_SCORES.get(event_type, 50.0)
        multiplier = 1.0
        reasons: list[str] = [f"Base {event_type.value} weight: {base}"]

        # 1. Outer planet involvement (slower moving = more profound generational & personal shift)
        if primary_body in cls.OUTER_PLANETS or (
            secondary_body and secondary_body in cls.OUTER_PLANETS
        ):
            multiplier *= 1.25
            reasons.append("Outer planet involvement (+25%)")

        # 2. Luminary or Angle involvement
        if (
            primary_body in cls.LUMINARIES
            or (secondary_body and secondary_body in cls.LUMINARIES)
            or (secondary_body and secondary_body in cls.ANGLES)
        ):
            multiplier *= 1.20
            reasons.append("Luminary or cardinal angle activation (+20%)")

        # 3. Major hard aspect multiplier (Conjunction, Opposition, Square)
        if aspect_type in (AspectType.CONJUNCTION, AspectType.OPPOSITION, AspectType.SQUARE):
            multiplier *= 1.15
            reasons.append("Dynamic hard aspect (+15%)")

        # 4. Exactness / tight orb bonus
        if is_exact or orb < 0.5:
            multiplier *= 1.10
            reasons.append("Exact peak aspect hit (+10%)")

        final_score = min(100.0, max(5.0, round(base * multiplier, 1)))

        if final_score >= 85.0:
            tier = EventSignificanceTier.PINNACLE
        elif final_score >= 70.0:
            tier = EventSignificanceTier.HIGH
        elif final_score >= 45.0:
            tier = EventSignificanceTier.MODERATE
        elif final_score >= 20.0:
            tier = EventSignificanceTier.MILD
        else:
            tier = EventSignificanceTier.BACKGROUND

        return EventScore(
            score=final_score,
            tier=tier,
            rationale="; ".join(reasons),
        )
