"""Detection of Lunar phases, New Moons, Full Moons, and Solar/Lunar Eclipses."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.astrology.ephemeris import EphemerisService
from app.config.constants import AstroEventType, AstrologySystem, Planet


@dataclass(frozen=True)
class LunarEventInfo:
    """Detected lunar phase or eclipse event."""

    event_type: AstroEventType
    phase_name: str  # "New Moon", "Full Moon", "Solar Eclipse", "Lunar Eclipse", "First Quarter", "Third Quarter"
    datetime_utc: datetime
    moon_sign: str
    moon_degree: float
    sun_sign: str
    sun_degree: float
    is_eclipse: bool
    description: str


class LunarEventDetector:
    """Calculates lunations and eclipse alignments over a given time window."""

    def __init__(self, ephemeris: EphemerisService | None = None) -> None:
        self.ephemeris = ephemeris or EphemerisService()

    def scan_lunar_events(
        self,
        start_utc: datetime,
        days: int = 30,
        step_hours: int = 6,
    ) -> list[LunarEventInfo]:
        """
        Scan a time interval for New Moons, Full Moons, and Eclipses using angular elongation zero-crossings.
        """
        start_utc = (
            start_utc.replace(tzinfo=UTC) if start_utc.tzinfo is None else start_utc.astimezone(UTC)
        )
        events: list[LunarEventInfo] = []

        total_steps = int((days * 24) / step_hours)

        prev_angle: float | None = None

        for step in range(total_steps + 1):
            curr_time = start_utc + timedelta(hours=step * step_hours)
            jd = self.ephemeris.datetime_to_julian_day(curr_time)

            sun_pos = self.ephemeris.calculate_planet(jd, Planet.SUN, AstrologySystem.WESTERN)
            moon_pos = self.ephemeris.calculate_planet(jd, Planet.MOON, AstrologySystem.WESTERN)
            node_pos = self.ephemeris.calculate_planet(
                jd, Planet.MEAN_NODE, AstrologySystem.WESTERN
            )

            # Ecliptic elongation: Moon - Sun modulo 360°
            curr_angle = (moon_pos.longitude - sun_pos.longitude) % 360.0

            if prev_angle is not None:
                # 1. New Moon (0° crossing)
                if prev_angle > 300.0 and curr_angle < 60.0:
                    # Check for eclipse proximity to Node (within 12°)
                    dist_to_node = min(
                        abs(moon_pos.longitude - node_pos.longitude) % 360.0,
                        360.0 - (abs(moon_pos.longitude - node_pos.longitude) % 360.0),
                    )
                    is_eclipse = (dist_to_node <= 12.0) or (abs(dist_to_node - 180.0) <= 12.0)
                    name = "Solar Eclipse" if is_eclipse else "New Moon"
                    evt_type = AstroEventType.ECLIPSE if is_eclipse else AstroEventType.LUNAR_PHASE

                    events.append(
                        LunarEventInfo(
                            event_type=evt_type,
                            phase_name=name,
                            datetime_utc=curr_time,
                            moon_sign=moon_pos.sign_name,
                            moon_degree=round(moon_pos.sign_longitude, 2),
                            sun_sign=sun_pos.sign_name,
                            sun_degree=round(sun_pos.sign_longitude, 2),
                            is_eclipse=is_eclipse,
                            description=(
                                f"{name} in {moon_pos.sign_name} at {round(moon_pos.sign_longitude, 1)}°. "
                                + (
                                    "Major karmic portal and potent new beginning."
                                    if is_eclipse
                                    else "Ideal time for intention setting and initiation."
                                )
                            ),
                        )
                    )

                # 2. Full Moon (180° crossing)
                elif prev_angle < 180.0 and curr_angle >= 180.0:
                    dist_to_node = min(
                        abs(moon_pos.longitude - node_pos.longitude) % 360.0,
                        360.0 - (abs(moon_pos.longitude - node_pos.longitude) % 360.0),
                    )
                    is_eclipse = (dist_to_node <= 12.0) or (abs(dist_to_node - 180.0) <= 12.0)
                    name = "Lunar Eclipse" if is_eclipse else "Full Moon"
                    evt_type = AstroEventType.ECLIPSE if is_eclipse else AstroEventType.LUNAR_PHASE

                    events.append(
                        LunarEventInfo(
                            event_type=evt_type,
                            phase_name=name,
                            datetime_utc=curr_time,
                            moon_sign=moon_pos.sign_name,
                            moon_degree=round(moon_pos.sign_longitude, 2),
                            sun_sign=sun_pos.sign_name,
                            sun_degree=round(sun_pos.sign_longitude, 2),
                            is_eclipse=is_eclipse,
                            description=(
                                f"{name} with Moon in {moon_pos.sign_name} opposing Sun in {sun_pos.sign_name}. "
                                + (
                                    "Culmination, emotional release, and karmic revelation."
                                    if is_eclipse
                                    else "Peak illumination, completion, and clarity."
                                )
                            ),
                        )
                    )

            prev_angle = curr_angle

        return events
