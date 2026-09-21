"""Ephemeris service wrapping Swiss Ephemeris (pyswisseph) with robust mathematical fallbacks."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime

from app.config.constants import (
    PLANET_NAMES,
    SIGN_NAMES,
    AstrologySystem,
    Ayanamsa,
    HouseSystem,
    Planet,
    Sign,
)
from app.config.settings import get_settings

try:
    import swisseph as swe

    SWISSEPH_AVAILABLE = True
except ImportError:
    try:
        import pyswisseph as swe

        SWISSEPH_AVAILABLE = True
    except ImportError:
        swe = None  # type: ignore[assignment]
        SWISSEPH_AVAILABLE = False


# Ayanamsa mappings to Swiss Ephemeris sidereal mode constants
AYANAMSA_MAP: dict[Ayanamsa, int] = {}
if SWISSEPH_AVAILABLE and swe is not None:
    AYANAMSA_MAP = {
        Ayanamsa.LAHIRI: getattr(swe, "SIDM_LAHIRI", 1),
        Ayanamsa.RAMAN: getattr(swe, "SIDM_RAMAN", 3),
        Ayanamsa.KRISHNAMURTI: getattr(swe, "SIDM_KRISHNAMURTI", 5),
        Ayanamsa.FAGAN_BRADLEY: getattr(swe, "SIDM_FAGAN_BRADLEY", 0),
        Ayanamsa.TRUE_CITRA: getattr(swe, "SIDM_TRUE_CITRA", 27),
    }


@dataclass(frozen=True)
class PlanetPosition:
    """Astronomical and astrological position of a celestial body."""

    planet_id: int
    name: str
    longitude: float  # Absolute ecliptic longitude [0, 360)
    latitude: float  # Ecliptic latitude [-90, 90]
    distance: float  # Distance in AU
    speed_longitude: float  # Speed in longitude (deg/day)
    is_retrograde: bool
    sign_index: int  # 0 = Aries .. 11 = Pisces
    sign_name: str
    sign_longitude: float  # Degree within the sign [0, 30)


@dataclass(frozen=True)
class HousePositions:
    """House cusps and principal chart angles."""

    system: str
    cusps: list[float]  # 12 house cusp longitudes [0, 360)
    ascendant: float  # Ascendant (1st house cusp / rising degree)
    midheaven: float  # Medium Coeli (MC / 10th house cusp)
    armc: float  # Right ascension of MC
    vertex: float  # Vertex degree


class EphemerisService:
    """High-precision astronomical calculation engine wrapping Swiss Ephemeris."""

    def __init__(self, ephe_path: str | None = None) -> None:
        settings = get_settings()
        self.ephe_path = ephe_path or settings.ephemeris_path
        if SWISSEPH_AVAILABLE and swe is not None and self.ephe_path:
            swe.set_ephe_path(self.ephe_path)

    @staticmethod
    def datetime_to_julian_day(dt_utc: datetime) -> float:
        """Convert a UTC datetime to Julian Day Number."""
        dt_utc = dt_utc.replace(tzinfo=UTC) if dt_utc.tzinfo is None else dt_utc.astimezone(UTC)

        year = dt_utc.year
        month = dt_utc.month
        day = dt_utc.day
        hour_fraction = (
            dt_utc.hour
            + dt_utc.minute / 60.0
            + (dt_utc.second + dt_utc.microsecond / 1_000_000.0) / 3600.0
        )

        if SWISSEPH_AVAILABLE and swe is not None:
            return swe.julday(year, month, day, hour_fraction, swe.GREG_CAL)

        # Standard Astronomical Julian Day formula fallback
        if month <= 2:
            year -= 1
            month += 12
        a = math.floor(year / 100)
        b = 2 - a + math.floor(a / 4)
        jd = (
            math.floor(365.25 * (year + 4716))
            + math.floor(30.6001 * (month + 1))
            + day
            + hour_fraction / 24.0
            + b
            - 1524.5
        )
        return jd

    def get_ayanamsa_value(self, jd: float, ayanamsa: Ayanamsa = Ayanamsa.LAHIRI) -> float:
        """Compute the ayanamsa (precession offset) for a Julian Day."""
        if SWISSEPH_AVAILABLE and swe is not None:
            mode = AYANAMSA_MAP.get(ayanamsa, swe.SIDM_LAHIRI)
            swe.set_sid_mode(mode, 0, 0)
            return swe.get_ayanamsa_ut(jd)

        # Approximate Lahiri ayanamsa formula: ~23.85° at epoch 2000.0, rate ~50.29 arcsec/year
        t = (jd - 2451545.0) / 36525.0
        return 23.856 + 1.396 * t

    def calculate_planet(
        self,
        jd: float,
        planet: Planet,
        system: AstrologySystem = AstrologySystem.WESTERN,
        ayanamsa: Ayanamsa = Ayanamsa.LAHIRI,
    ) -> PlanetPosition:
        """Calculate position and state of a planet."""
        planet_name = PLANET_NAMES.get(planet, f"Planet_{int(planet)}")

        if SWISSEPH_AVAILABLE and swe is not None:
            flags = swe.FLG_SWIEPH | swe.FLG_SPEED
            if system == AstrologySystem.VEDIC:
                mode = AYANAMSA_MAP.get(ayanamsa, swe.SIDM_LAHIRI)
                swe.set_sid_mode(mode, 0, 0)
                flags |= swe.FLG_SIDEREAL

            # Handle Ketu derived from Rahu
            if planet_name == "Ketu":
                res, _ = swe.calc_ut(jd, swe.MEAN_NODE, flags)
                lon = (res[0] + 180.0) % 360.0
                lat = -res[1]
                dist = res[2]
                speed = res[3]
            else:
                swe_planet_id = int(planet)
                res, _ = swe.calc_ut(jd, swe_planet_id, flags)
                lon = res[0] % 360.0
                lat = res[1]
                dist = res[2]
                speed = res[3]
        else:
            # Mathematical fallback approximation
            d = jd - 2451545.0
            base_lons = {
                Planet.SUN: (280.460 + 0.9856474 * d) % 360.0,
                Planet.MOON: (218.316 + 13.176396 * d) % 360.0,
                Planet.MERCURY: (355.433 + 4.0923344 * d) % 360.0,
                Planet.VENUS: (181.979 + 1.602130 * d) % 360.0,
                Planet.MARS: (355.433 + 0.524033 * d) % 360.0,
                Planet.JUPITER: (34.351 + 0.083085 * d) % 360.0,
                Planet.SATURN: (50.077 + 0.033459 * d) % 360.0,
                Planet.URANUS: (314.055 + 0.011728 * d) % 360.0,
                Planet.NEPTUNE: (304.348 + 0.005981 * d) % 360.0,
                Planet.PLUTO: (238.966 + 0.003975 * d) % 360.0,
                Planet.MEAN_NODE: (125.044 - 0.0529539 * d) % 360.0,
            }
            lon = base_lons.get(planet, (280.0 + d) % 360.0)
            if system == AstrologySystem.VEDIC:
                ayan_val = self.get_ayanamsa_value(jd, ayanamsa)
                lon = (lon - ayan_val) % 360.0
            lat = 0.0
            dist = 1.0
            speed = 1.0 if planet != Planet.MEAN_NODE else -0.05

        sign_idx = int(lon // 30)
        sign_deg = lon % 30.0
        sign_enum = Sign(sign_idx)
        sign_title = SIGN_NAMES[sign_enum]
        is_retrograde = speed < 0.0 and planet not in (Planet.SUN, Planet.MOON)

        return PlanetPosition(
            planet_id=int(planet),
            name=planet_name,
            longitude=round(lon, 6),
            latitude=round(lat, 6),
            distance=round(dist, 6),
            speed_longitude=round(speed, 6),
            is_retrograde=is_retrograde,
            sign_index=sign_idx,
            sign_name=sign_title,
            sign_longitude=round(sign_deg, 6),
        )

    def calculate_houses(
        self,
        jd: float,
        latitude: float,
        longitude: float,
        house_system: HouseSystem = HouseSystem.PLACIDUS,
        system: AstrologySystem = AstrologySystem.WESTERN,
        ayanamsa: Ayanamsa = Ayanamsa.LAHIRI,
    ) -> HousePositions:
        """Calculate the 12 house cusps and angles (Ascendant, MC, Vertex)."""
        sys_code = house_system.to_swisseph_char()

        if SWISSEPH_AVAILABLE and swe is not None:
            if system == AstrologySystem.VEDIC:
                mode = AYANAMSA_MAP.get(ayanamsa, swe.SIDM_LAHIRI)
                swe.set_sid_mode(mode, 0, 0)
                # In Vedic, Whole Sign or Equal houses are standard
                cusps_res, ascmc = swe.houses_ex(
                    jd, latitude, longitude, sys_code.encode("ascii"), swe.FLG_SIDEREAL
                )
            else:
                cusps_res, ascmc = swe.houses(jd, latitude, longitude, sys_code.encode("ascii"))

            # Swiss ephemeris returns 1-indexed cusps (13 elements: index 0 unused)
            cusps = [cusps_res[i] % 360.0 for i in range(1, 13)]
            ascendant = ascmc[0] % 360.0
            midheaven = ascmc[1] % 360.0
            armc = ascmc[2] % 360.0
            vertex = ascmc[3] % 360.0
        else:
            # Fallback house calculation
            # RAMC = (Greenwich Mean Sidereal Time in deg + Longitude) % 360
            # Rough ascendant estimate
            d = jd - 2451545.0
            gmst = (280.46061837 + 360.98564736629 * d) % 360.0
            ramc = (gmst + longitude) % 360.0
            ascendant = (ramc + 90.0) % 360.0
            if system == AstrologySystem.VEDIC:
                ayan_val = self.get_ayanamsa_value(jd, ayanamsa)
                ascendant = (ascendant - ayan_val) % 360.0
            midheaven = ramc % 360.0
            cusps = [(ascendant + i * 30.0) % 360.0 for i in range(12)]
            armc = ramc
            vertex = (ascendant + 180.0) % 360.0

        return HousePositions(
            system=house_system.value,
            cusps=[round(c, 6) for c in cusps],
            ascendant=round(ascendant, 6),
            midheaven=round(midheaven, 6),
            armc=round(armc, 6),
            vertex=round(vertex, 6),
        )

    def calculate_all_planets(
        self,
        jd: float,
        system: AstrologySystem = AstrologySystem.WESTERN,
        ayanamsa: Ayanamsa = Ayanamsa.LAHIRI,
    ) -> dict[str, PlanetPosition]:
        """Calculate positions for standard planets and lunar nodes."""
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
        positions: dict[str, PlanetPosition] = {}
        for p in planets_to_calc:
            pos = self.calculate_planet(jd, p, system=system, ayanamsa=ayanamsa)
            positions[pos.name] = pos

        # Add Ketu
        rahu_pos = positions.get("North Node") or positions.get("Planet_10")
        if rahu_pos:
            ketu_lon = (rahu_pos.longitude + 180.0) % 360.0
            ketu_sign_idx = int(ketu_lon // 30)
            positions["Ketu"] = PlanetPosition(
                planet_id=100,
                name="Ketu",
                longitude=round(ketu_lon, 6),
                latitude=-rahu_pos.latitude,
                distance=rahu_pos.distance,
                speed_longitude=rahu_pos.speed_longitude,
                is_retrograde=True,
                sign_index=ketu_sign_idx,
                sign_name=SIGN_NAMES[Sign(ketu_sign_idx)],
                sign_longitude=round(ketu_lon % 30.0, 6),
            )

        return positions


ephemeris_service = EphemerisService()
