"""Unified AstroEventDetector orchestrating mundane and personalized event discovery and ranking."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from app.astro_events.lunar_events import LunarEventDetector
from app.astro_events.planetary_events import PlanetaryEventDetector
from app.astro_events.retrogrades import RetrogradeDetector
from app.astro_events.significance import EventRanker, EventSignificanceTier
from app.astro_events.transit_events import TransitEventDetector
from app.astrology.ephemeris import EphemerisService, PlanetPosition
from app.config.constants import AstroEventType


@dataclass(frozen=True)
class DetectedAstroEvent:
    """Unified standardized Astrological Event model."""

    title: str
    event_type: AstroEventType
    datetime_utc: datetime
    primary_body: str
    secondary_body: str | None
    sign_name: str | None
    degree: float | None
    aspect_type: str | None
    score: float  # 0 to 100
    significance_tier: EventSignificanceTier
    rationale: str
    description: str

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "event_type": self.event_type.value,
            "datetime_utc": self.datetime_utc.isoformat(),
            "primary_body": self.primary_body,
            "secondary_body": self.secondary_body,
            "sign_name": self.sign_name,
            "degree": self.degree,
            "aspect_type": self.aspect_type,
            "score": self.score,
            "significance_tier": self.significance_tier.value,
            "rationale": self.rationale,
            "description": self.description,
        }


class AstroEventDetector:
    """Orchestrator for discovering and ranking astrological events."""

    def __init__(self, ephemeris: EphemerisService | None = None) -> None:
        self.ephemeris = ephemeris or EphemerisService()
        self.lunar = LunarEventDetector(self.ephemeris)
        self.retrogrades = RetrogradeDetector(self.ephemeris)
        self.planetary = PlanetaryEventDetector(self.ephemeris)
        self.transit_hits = TransitEventDetector(self.ephemeris)

    def detect_mundane_events(
        self,
        start_utc: datetime,
        days: int = 30,
        min_score: float = 0.0,
    ) -> list[DetectedAstroEvent]:
        """
        Scan sky for all global astrological events (Lunations, Eclipses, Retrogrades, Ingresses, Cazimi).
        """
        start_utc = (
            start_utc.replace(tzinfo=UTC) if start_utc.tzinfo is None else start_utc.astimezone(UTC)
        )
        events: list[DetectedAstroEvent] = []

        # 1. Lunations & Eclipses
        lunations = self.lunar.scan_lunar_events(start_utc, days=days)
        for l_evt in lunations:
            score_info = EventRanker.rank_event(
                event_type=l_evt.event_type,
                primary_body="Moon",
                secondary_body="Sun",
                is_exact=True,
            )
            events.append(
                DetectedAstroEvent(
                    title=l_evt.phase_name,
                    event_type=l_evt.event_type,
                    datetime_utc=l_evt.datetime_utc,
                    primary_body="Moon",
                    secondary_body="Sun",
                    sign_name=l_evt.moon_sign,
                    degree=l_evt.moon_degree,
                    aspect_type="conjunction"
                    if "New" in l_evt.phase_name or "Solar" in l_evt.phase_name
                    else "opposition",
                    score=score_info.score,
                    significance_tier=score_info.tier,
                    rationale=score_info.rationale,
                    description=l_evt.description,
                )
            )

        # 2. Retrogrades
        stations = self.retrogrades.scan_stations(start_utc, days=days)
        for s_evt in stations:
            score_info = EventRanker.rank_event(
                event_type=s_evt.event_type,
                primary_body=s_evt.planet_name,
                is_exact=True,
            )
            events.append(
                DetectedAstroEvent(
                    title=f"{s_evt.planet_name} Stations {'Retrograde' if s_evt.is_retrograde_now else 'Direct'}",
                    event_type=s_evt.event_type,
                    datetime_utc=s_evt.datetime_utc,
                    primary_body=s_evt.planet_name,
                    secondary_body=None,
                    sign_name=s_evt.sign_name,
                    degree=s_evt.degree_in_sign,
                    aspect_type=None,
                    score=score_info.score,
                    significance_tier=score_info.tier,
                    rationale=score_info.rationale,
                    description=s_evt.description,
                )
            )

        # 3. Ingresses
        ingresses = self.planetary.scan_ingresses(start_utc, days=days)
        for i_evt in ingresses:
            score_info = EventRanker.rank_event(
                event_type=i_evt.event_type,
                primary_body=i_evt.primary_planet,
                is_exact=True,
            )
            events.append(
                DetectedAstroEvent(
                    title=i_evt.name,
                    event_type=i_evt.event_type,
                    datetime_utc=i_evt.datetime_utc,
                    primary_body=i_evt.primary_planet,
                    secondary_body=None,
                    sign_name=i_evt.sign_name,
                    degree=0.0,
                    aspect_type=None,
                    score=score_info.score,
                    significance_tier=score_info.tier,
                    rationale=score_info.rationale,
                    description=i_evt.description,
                )
            )

        # Filter by minimum score and sort by score (descending) & date
        filtered = [e for e in events if e.score >= min_score]
        filtered.sort(key=lambda e: (-e.score, e.datetime_utc))
        return filtered

    def detect_personalized_events(
        self,
        natal_planets: list[PlanetPosition],
        start_utc: datetime,
        days: int = 30,
        min_score: float = 0.0,
    ) -> list[DetectedAstroEvent]:
        """
        Scan and rank personalized transit events hitting a user's natal chart.
        """
        start_utc = (
            start_utc.replace(tzinfo=UTC) if start_utc.tzinfo is None else start_utc.astimezone(UTC)
        )
        events: list[DetectedAstroEvent] = []

        # 1. Personalized Transit Aspect Hits
        transit_hits = self.transit_hits.scan_personalized_transits(
            natal_planets=natal_planets,
            start_utc=start_utc,
            days=days,
        )

        for th in transit_hits:
            score_info = EventRanker.rank_event(
                event_type=AstroEventType.TRANSIT_TO_NATAL,
                primary_body=th.transiting_body,
                secondary_body=th.natal_body,
                aspect_type=th.aspect_type,
                is_exact=th.orb < 0.25,
                orb=th.orb,
            )
            events.append(
                DetectedAstroEvent(
                    title=f"Transit {th.transiting_body} {th.aspect_type.value} Natal {th.natal_body}",
                    event_type=th.event_type,
                    datetime_utc=th.exact_datetime_utc,
                    primary_body=th.transiting_body,
                    secondary_body=th.natal_body,
                    sign_name=None,
                    degree=th.transit_longitude,
                    aspect_type=th.aspect_type.value,
                    score=score_info.score,
                    significance_tier=score_info.tier,
                    rationale=score_info.rationale,
                    description=th.description,
                )
            )

        # Also include major mundane events (Lunations, Eclipses)
        mundane = self.detect_mundane_events(start_utc=start_utc, days=days, min_score=min_score)
        events.extend(mundane)

        filtered = [e for e in events if e.score >= min_score]
        filtered.sort(key=lambda e: (-e.score, e.datetime_utc))
        return filtered
