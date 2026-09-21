"""Detection of Planetary Ingresses, Combustions, Cazimi, and Major Sky Conjunctions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.astrology.ephemeris import EphemerisService
from app.config.constants import AstroEventType, AstrologySystem, Planet


@dataclass(frozen=True)
class PlanetaryEventInfo:
    """Detected mundane planetary alignment or ingress."""

    event_type: AstroEventType
    name: str
    primary_planet: str
    secondary_planet: str | None
    datetime_utc: datetime
    sign_name: str
    degree_in_sign: float
    description: str


class PlanetaryEventDetector:
    """Detects ingresses, combustions, cazimi, and conjunctions in the sky."""

    COMBUSTION_ORBS: dict[str, float] = {
        "Moon": 12.0,
        "Mars": 17.0,
        "Mercury": 12.0,
        "Venus": 8.0,
        "Jupiter": 11.0,
        "Saturn": 15.0,
    }

    CAZIMI_ORB: float = 17.0 / 60.0  # 17 arcminutes = ~0.2833°

    def __init__(self, ephemeris: EphemerisService | None = None) -> None:
        self.ephemeris = ephemeris or EphemerisService()

    def scan_ingresses(
        self,
        start_utc: datetime,
        days: int = 30,
        step_days: int = 1,
    ) -> list[PlanetaryEventInfo]:
        """Detect when planets change signs over a time window."""
        start_utc = (
            start_utc.replace(tzinfo=UTC) if start_utc.tzinfo is None else start_utc.astimezone(UTC)
        )
        events: list[PlanetaryEventInfo] = []

        planets_to_track = [
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

        for p in planets_to_track:
            prev_sign_idx: int | None = None

            for d in range(0, days + 1, step_days):
                curr_time = start_utc + timedelta(days=d)
                jd = self.ephemeris.datetime_to_julian_day(curr_time)
                pos = self.ephemeris.calculate_planet(jd, p, AstrologySystem.WESTERN)

                if prev_sign_idx is not None and pos.sign_index != prev_sign_idx:
                    sign_name = pos.sign_name
                    events.append(
                        PlanetaryEventInfo(
                            event_type=AstroEventType.PLANETARY_INGRESS,
                            name=f"{pos.name} enters {sign_name}",
                            primary_planet=pos.name,
                            secondary_planet=None,
                            datetime_utc=curr_time,
                            sign_name=sign_name,
                            degree_in_sign=0.0,
                            description=f"{pos.name} ingresses into {sign_name}, shifting the energetic archetype for its expressions.",
                        )
                    )

                prev_sign_idx = pos.sign_index

        events.sort(key=lambda e: e.datetime_utc)
        return events

    def check_cazimi_and_combustion(
        self,
        target_utc: datetime,
    ) -> list[PlanetaryEventInfo]:
        """Check if any planets are currently Combust or in Cazimi (in the heart of the Sun)."""
        target_utc = (
            target_utc.replace(tzinfo=UTC)
            if target_utc.tzinfo is None
            else target_utc.astimezone(UTC)
        )
        jd = self.ephemeris.datetime_to_julian_day(target_utc)

        sun_pos = self.ephemeris.calculate_planet(jd, Planet.SUN, AstrologySystem.WESTERN)
        events: list[PlanetaryEventInfo] = []

        planets_to_check = [
            Planet.MOON,
            Planet.MERCURY,
            Planet.VENUS,
            Planet.MARS,
            Planet.JUPITER,
            Planet.SATURN,
        ]

        for p in planets_to_check:
            pos = self.ephemeris.calculate_planet(jd, p, AstrologySystem.WESTERN)
            dist = min(
                abs(pos.longitude - sun_pos.longitude) % 360.0,
                360.0 - (abs(pos.longitude - sun_pos.longitude) % 360.0),
            )

            if dist <= self.CAZIMI_ORB:
                events.append(
                    PlanetaryEventInfo(
                        event_type=AstroEventType.MAJOR_ASPECT,
                        name=f"{pos.name} Cazimi (Heart of the Sun)",
                        primary_planet=pos.name,
                        secondary_planet="Sun",
                        datetime_utc=target_utc,
                        sign_name=pos.sign_name,
                        degree_in_sign=round(pos.sign_longitude, 2),
                        description=f"{pos.name} is purified in the exact heart of the Sun (Cazimi) at {round(pos.sign_longitude, 1)}° {pos.sign_name} — an extremely potent window of empowerment and spiritual illumination.",
                    )
                )
            elif dist <= self.COMBUSTION_ORBS.get(pos.name, 10.0):
                events.append(
                    PlanetaryEventInfo(
                        event_type=AstroEventType.MAJOR_ASPECT,
                        name=f"{pos.name} Combust by Sun",
                        primary_planet=pos.name,
                        secondary_planet="Sun",
                        datetime_utc=target_utc,
                        sign_name=pos.sign_name,
                        degree_in_sign=round(pos.sign_longitude, 2),
                        description=f"{pos.name} is within combustion orb of the Sun ({round(dist, 1)}°), drawing its outward expressions inward.",
                    )
                )

        return events
