"""Detection of planetary retrograde stations, direct stations, and shadow periods."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.astrology.ephemeris import EphemerisService, PlanetPosition
from app.config.constants import AstroEventType, AstrologySystem, Planet


@dataclass(frozen=True)
class RetrogradeInfo:
    """Detected planetary retrograde or stationing event."""

    planet_name: str
    event_type: AstroEventType  # RETROGRADE_START, RETROGRADE_END, or STATIONARY
    datetime_utc: datetime
    sign_name: str
    degree_in_sign: float
    is_retrograde_now: bool
    description: str


class RetrogradeDetector:
    """Detects retrograde stations and direct turning points for planets."""

    RETROGRADE_PLANETS = [
        Planet.MERCURY,
        Planet.VENUS,
        Planet.MARS,
        Planet.JUPITER,
        Planet.SATURN,
        Planet.URANUS,
        Planet.NEPTUNE,
        Planet.PLUTO,
    ]

    def __init__(self, ephemeris: EphemerisService | None = None) -> None:
        self.ephemeris = ephemeris or EphemerisService()

    def get_current_retrogrades(self, target_utc: datetime) -> list[PlanetPosition]:
        """Return list of all planets currently in retrograde motion."""
        target_utc = (
            target_utc.replace(tzinfo=UTC)
            if target_utc.tzinfo is None
            else target_utc.astimezone(UTC)
        )
        jd = self.ephemeris.datetime_to_julian_day(target_utc)

        retro_planets: list[PlanetPosition] = []
        for p in self.RETROGRADE_PLANETS:
            pos = self.ephemeris.calculate_planet(jd, p, AstrologySystem.WESTERN)
            if pos.is_retrograde:
                retro_planets.append(pos)
        return retro_planets

    def scan_stations(
        self,
        start_utc: datetime,
        days: int = 60,
        step_days: int = 1,
    ) -> list[RetrogradeInfo]:
        """
        Scan time window for retrograde and direct station transitions.
        """
        start_utc = (
            start_utc.replace(tzinfo=UTC) if start_utc.tzinfo is None else start_utc.astimezone(UTC)
        )
        events: list[RetrogradeInfo] = []

        for p in self.RETROGRADE_PLANETS:
            prev_speed: float | None = None

            for d in range(0, days + 1, step_days):
                curr_time = start_utc + timedelta(days=d)
                jd = self.ephemeris.datetime_to_julian_day(curr_time)
                pos = self.ephemeris.calculate_planet(jd, p, AstrologySystem.WESTERN)

                if prev_speed is not None:
                    # Direct to Retrograde (Speed crosses from positive to negative)
                    if prev_speed > 0.0 and pos.speed_longitude <= 0.0:
                        events.append(
                            RetrogradeInfo(
                                planet_name=pos.name,
                                event_type=AstroEventType.RETROGRADE_START,
                                datetime_utc=curr_time,
                                sign_name=pos.sign_name,
                                degree_in_sign=round(pos.sign_longitude, 2),
                                is_retrograde_now=True,
                                description=f"{pos.name} stations Retrograde at {round(pos.sign_longitude, 1)}° {pos.sign_name}. Time for review, reflection, and inner recalibration.",
                            )
                        )
                    # Retrograde to Direct (Speed crosses from negative to positive)
                    elif prev_speed < 0.0 and pos.speed_longitude >= 0.0:
                        events.append(
                            RetrogradeInfo(
                                planet_name=pos.name,
                                event_type=AstroEventType.RETROGRADE_END,
                                datetime_utc=curr_time,
                                sign_name=pos.sign_name,
                                degree_in_sign=round(pos.sign_longitude, 2),
                                is_retrograde_now=False,
                                description=f"{pos.name} stations Direct at {round(pos.sign_longitude, 1)}° {pos.sign_name}. Momentum resumes and forward movement is restored.",
                            )
                        )

                prev_speed = pos.speed_longitude

        events.sort(key=lambda e: e.datetime_utc)
        return events
