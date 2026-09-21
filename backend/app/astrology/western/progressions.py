"""Secondary progressions calculation engine (day-for-a-year)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.astrology.ephemeris import EphemerisService, HousePositions, PlanetPosition
from app.astrology.western.aspects import AspectCalculator, AspectInfo
from app.config.constants import AstrologySystem, HouseSystem, Planet


@dataclass(frozen=True)
class ProgressedChartResult:
    """Comprehensive secondary progressed chart result."""

    progressed_datetime_utc: datetime
    age_in_years: float
    target_datetime_utc: datetime
    progressed_planets: list[PlanetPosition]
    progressed_houses: HousePositions
    progressed_to_natal_aspects: list[AspectInfo]


class SecondaryProgressionsCalculator:
    """
    Calculates Secondary Progressions using the classical Major Progression formula (1 day = 1 year).
    """

    TROPICAL_YEAR_DAYS: float = 365.242199

    def __init__(self, ephemeris: EphemerisService | None = None) -> None:
        self.ephemeris = ephemeris or EphemerisService()

    def calculate_progressions(
        self,
        birth_utc: datetime,
        latitude: float,
        longitude: float,
        target_utc: datetime,
        natal_planets: list[PlanetPosition],
        house_system: HouseSystem = HouseSystem.PLACIDUS,
    ) -> ProgressedChartResult:
        """
        Compute secondary progressions for a given target date.
        """
        birth_utc = (
            birth_utc.replace(tzinfo=UTC) if birth_utc.tzinfo is None else birth_utc.astimezone(UTC)
        )
        target_utc = (
            target_utc.replace(tzinfo=UTC)
            if target_utc.tzinfo is None
            else target_utc.astimezone(UTC)
        )

        diff_seconds = (target_utc - birth_utc).total_seconds()
        age_years = diff_seconds / (self.TROPICAL_YEAR_DAYS * 86400.0)

        # Progressed moment = birth moment + age_in_days
        progressed_moment = birth_utc + timedelta(days=age_years)
        progressed_jd = self.ephemeris.datetime_to_julian_day(progressed_moment)

        # Progressed planets (Sun through Pluto + Nodes)
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

        prog_planets = [
            self.ephemeris.calculate_planet(
                jd=progressed_jd,
                planet=p,
                system=AstrologySystem.WESTERN,
            )
            for p in planets_to_calc
        ]

        prog_houses = self.ephemeris.calculate_houses(
            jd=progressed_jd,
            latitude=latitude,
            longitude=longitude,
            system=house_system,
        )

        # Progressed-to-Natal Aspects (tight orb <= 1.5° for progressions)
        from app.config.constants import ASPECT_ANGLES

        prog_aspects: list[AspectInfo] = []
        for p_prog in prog_planets:
            for p_nat in natal_planets:
                actual_dist = AspectCalculator.calculate_angular_distance(
                    p_prog.longitude, p_nat.longitude
                )
                for a_type, target_angle in ASPECT_ANGLES.items():
                    if a_type not in AspectCalculator.MAJOR_ASPECTS:
                        continue
                    orb = abs(actual_dist - target_angle)
                    if orb <= 1.5:
                        is_app = AspectCalculator.is_aspect_applying(p_prog, p_nat, target_angle)
                        prog_aspects.append(
                            AspectInfo(
                                planet_1=f"Prog {p_prog.name}",
                                planet_2=f"Natal {p_nat.name}",
                                aspect_type=a_type,
                                angle=target_angle,
                                actual_angle=round(actual_dist, 4),
                                orb=round(orb, 4),
                                max_orb=1.5,
                                is_applying=is_app,
                                is_major=True,
                            )
                        )

        prog_aspects.sort(key=lambda a: a.orb)

        return ProgressedChartResult(
            progressed_datetime_utc=progressed_moment,
            age_in_years=round(age_years, 4),
            target_datetime_utc=target_utc,
            progressed_planets=prog_planets,
            progressed_houses=prog_houses,
            progressed_to_natal_aspects=prog_aspects,
        )
