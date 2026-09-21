"""Transit event scanning over date windows detecting exact aspect hits against natal positions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.astrology.ephemeris import EphemerisService, PlanetPosition
from app.astrology.western.aspects import AspectCalculator
from app.config.constants import ASPECT_ANGLES, AspectType, AstroEventType, AstrologySystem, Planet


@dataclass(frozen=True)
class TransitHitEvent:
    """Exact or peak aspect event between a transiting planet and a natal point."""

    event_type: AstroEventType
    transiting_body: str
    natal_body: str
    aspect_type: AspectType
    exact_datetime_utc: datetime
    transit_longitude: float
    natal_longitude: float
    orb: float
    description: str


class TransitEventDetector:
    """Scans for exact transit aspect hits to natal chart points over specified time ranges."""

    def __init__(self, ephemeris: EphemerisService | None = None) -> None:
        self.ephemeris = ephemeris or EphemerisService()

    def scan_personalized_transits(
        self,
        natal_planets: list[PlanetPosition],
        start_utc: datetime,
        days: int = 30,
        step_days: int = 1,
    ) -> list[TransitHitEvent]:
        """
        Scan a time interval for exact transit aspect events hitting a user's natal chart.
        """
        start_utc = (
            start_utc.replace(tzinfo=UTC) if start_utc.tzinfo is None else start_utc.astimezone(UTC)
        )
        hits: list[TransitHitEvent] = []

        transiting_bodies = [
            Planet.SUN,
            Planet.MERCURY,
            Planet.VENUS,
            Planet.MARS,
            Planet.JUPITER,
            Planet.SATURN,
            Planet.URANUS,
            Planet.NEPTUNE,
            Planet.PLUTO,
        ]

        for d in range(0, days + 1, step_days):
            curr_time = start_utc + timedelta(days=d)
            jd = self.ephemeris.datetime_to_julian_day(curr_time)

            for tp in transiting_bodies:
                t_pos = self.ephemeris.calculate_planet(jd, tp, AstrologySystem.WESTERN)

                for np in natal_planets:
                    dist = AspectCalculator.calculate_angular_distance(
                        t_pos.longitude, np.longitude
                    )

                    for a_type in (
                        AspectType.CONJUNCTION,
                        AspectType.OPPOSITION,
                        AspectType.TRINE,
                        AspectType.SQUARE,
                        AspectType.SEXTILE,
                    ):
                        target_angle = ASPECT_ANGLES[a_type]
                        orb = abs(dist - target_angle)

                        # Peak exact aspect threshold (within ~1.0 degree)
                        if orb <= 1.0:
                            hits.append(
                                TransitHitEvent(
                                    event_type=AstroEventType.TRANSIT_TO_NATAL,
                                    transiting_body=t_pos.name,
                                    natal_body=np.name,
                                    aspect_type=a_type,
                                    exact_datetime_utc=curr_time,
                                    transit_longitude=round(t_pos.longitude, 4),
                                    natal_longitude=round(np.longitude, 4),
                                    orb=round(orb, 4),
                                    description=(
                                        f"Transiting {t_pos.name} forms exact {a_type.value} to natal {np.name} "
                                        f"({round(orb, 2)}° orb). Catalyst for activation in personal timing."
                                    ),
                                )
                            )

        # Deduplicate and sort by closest orb / chronological order
        hits.sort(key=lambda h: (h.exact_datetime_utc, h.orb))
        return hits
