"""Western astrology transits calculator against natal positions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from app.astrology.ephemeris import EphemerisService, PlanetPosition
from app.astrology.western.aspects import AspectCalculator
from app.astrology.western.houses import WesternHouseCalculator
from app.config.constants import ASPECT_ANGLES, AspectType, AstrologySystem, Planet


@dataclass(frozen=True)
class TransitHit:
    """A specific transit aspect hitting a natal point."""

    transiting_planet: str
    natal_point: str
    aspect_type: AspectType
    angle: float
    actual_angle: float
    orb: float
    is_applying: bool
    transit_longitude: float
    natal_longitude: float


@dataclass(frozen=True)
class TransitHousePosition:
    """Information on which natal house a transiting planet is currently activating."""

    planet_name: str
    transit_longitude: float
    natal_house: int


@dataclass(frozen=True)
class WesternTransitResult:
    """Comprehensive Western transit analysis result."""

    transit_datetime_utc: datetime
    transiting_planets: list[PlanetPosition]
    transit_to_natal_aspects: list[TransitHit]
    transits_in_natal_houses: list[TransitHousePosition]


class WesternTransitCalculator:
    """Calculates real-time or historical transit positions and aspects against a natal chart."""

    def __init__(self, ephemeris: EphemerisService | None = None) -> None:
        self.ephemeris = ephemeris or EphemerisService()

    def calculate_transits(
        self,
        natal_planets: list[PlanetPosition],
        natal_house_cusps: list[float],
        transit_utc: datetime,
        aspect_orb: float = 3.5,
    ) -> WesternTransitResult:
        """
        Compute transiting planets at transit_utc and compare against natal chart.
        """
        transit_utc = (
            transit_utc.replace(tzinfo=UTC)
            if transit_utc.tzinfo is None
            else transit_utc.astimezone(UTC)
        )
        jd = self.ephemeris.datetime_to_julian_day(transit_utc)

        planets_to_calc = [
            Planet.SUN,
            Planet.MOON,
            Planet.MERCURY,
            Planet.VENUS,
            Planet.MARS,
            Planet.JUPITER,
            Planet.SATURN,
            Planet.URANUS,
            Planet.NEPTUNE,
            Planet.PLUTO,
            Planet.MEAN_NODE,
        ]

        transiting_planets = [
            self.ephemeris.calculate_planet(
                jd=jd,
                planet=p,
                system=AstrologySystem.WESTERN,
            )
            for p in planets_to_calc
        ]

        # 1. Transit-to-Natal Aspects
        transit_aspects: list[TransitHit] = []
        for t_planet in transiting_planets:
            for n_planet in natal_planets:
                actual_dist = AspectCalculator.calculate_angular_distance(
                    t_planet.longitude, n_planet.longitude
                )
                for a_type, target_angle in ASPECT_ANGLES.items():
                    if a_type not in AspectCalculator.MAJOR_ASPECTS:
                        continue

                    max_orb = aspect_orb
                    # Tighter orb for minor aspects or outer transits if needed
                    orb = abs(actual_dist - target_angle)
                    if orb <= max_orb:
                        is_app = AspectCalculator.is_aspect_applying(
                            t_planet, n_planet, target_angle
                        )
                        transit_aspects.append(
                            TransitHit(
                                transiting_planet=t_planet.name,
                                natal_point=n_planet.name,
                                aspect_type=a_type,
                                angle=target_angle,
                                actual_angle=round(actual_dist, 4),
                                orb=round(orb, 4),
                                is_applying=is_app,
                                transit_longitude=round(t_planet.longitude, 4),
                                natal_longitude=round(n_planet.longitude, 4),
                            )
                        )

        transit_aspects.sort(key=lambda a: a.orb)

        # 2. Transits in Natal Houses
        transit_houses = [
            TransitHousePosition(
                planet_name=tp.name,
                transit_longitude=round(tp.longitude, 4),
                natal_house=WesternHouseCalculator.get_house_for_longitude(
                    tp.longitude, natal_house_cusps
                ),
            )
            for tp in transiting_planets
        ]

        return WesternTransitResult(
            transit_datetime_utc=transit_utc,
            transiting_planets=transiting_planets,
            transit_to_natal_aspects=transit_aspects,
            transits_in_natal_houses=transit_houses,
        )
