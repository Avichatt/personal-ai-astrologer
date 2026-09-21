"""Western astrology house calculation and analysis."""

from __future__ import annotations

from dataclasses import dataclass

from app.config.constants import SIGN_NAMES, HouseSystem, Planet, Sign

# Traditional and Modern planetary rulers for Western signs
TRADITIONAL_RULERS: dict[Sign, Planet] = {
    Sign.ARIES: Planet.MARS,
    Sign.TAURUS: Planet.VENUS,
    Sign.GEMINI: Planet.MERCURY,
    Sign.CANCER: Planet.MOON,
    Sign.LEO: Planet.SUN,
    Sign.VIRGO: Planet.MERCURY,
    Sign.LIBRA: Planet.VENUS,
    Sign.SCORPIO: Planet.MARS,
    Sign.SAGITTARIUS: Planet.JUPITER,
    Sign.CAPRICORN: Planet.SATURN,
    Sign.AQUARIUS: Planet.SATURN,
    Sign.PISCES: Planet.JUPITER,
}

MODERN_RULERS: dict[Sign, Planet] = {
    Sign.ARIES: Planet.MARS,
    Sign.TAURUS: Planet.VENUS,
    Sign.GEMINI: Planet.MERCURY,
    Sign.CANCER: Planet.MOON,
    Sign.LEO: Planet.SUN,
    Sign.VIRGO: Planet.MERCURY,
    Sign.LIBRA: Planet.VENUS,
    Sign.SCORPIO: Planet.PLUTO,
    Sign.SAGITTARIUS: Planet.JUPITER,
    Sign.CAPRICORN: Planet.SATURN,
    Sign.AQUARIUS: Planet.URANUS,
    Sign.PISCES: Planet.NEPTUNE,
}


@dataclass(frozen=True)
class WesternHouseInfo:
    """Detailed information for an individual astrological house."""

    house_number: int  # 1 through 12
    cusp_longitude: float  # Absolute ecliptic longitude [0, 360)
    sign_index: int  # 0 = Aries .. 11 = Pisces
    sign_name: str
    degree_in_sign: float  # [0, 30)
    traditional_ruler: str
    modern_ruler: str
    occupants: list[str]  # Names of planets occupying this house


class WesternHouseCalculator:
    """Calculates house placements, cusp assignments, and planetary house occupancy."""

    @staticmethod
    def get_house_for_longitude(longitude: float, house_cusps: list[float]) -> int:
        """
        Determine which house (1-12) a given ecliptic longitude falls into.

        Assumes house_cusps is a 12-element list of cusp degrees in order [H1, H2, ..., H12].
        Correctly handles the 360° circular boundary.
        """
        lon = longitude % 360.0

        for i in range(12):
            start = house_cusps[i] % 360.0
            next_idx = (i + 1) % 12
            end = house_cusps[next_idx] % 360.0

            if start < end:
                if start <= lon < end:
                    return i + 1
            else:
                # Segment crosses 0° Aries
                if lon >= start or lon < end:
                    return i + 1

        return 1  # Fallback

    @classmethod
    def analyze_houses(
        cls,
        house_cusps: list[float],
        planet_positions: dict[str, float],
        system: HouseSystem = HouseSystem.PLACIDUS,
    ) -> list[WesternHouseInfo]:
        """
        Construct WesternHouseInfo for all 12 houses including occupant lists.

        planet_positions: mapping of planet_name -> longitude.
        """
        # Group occupants by house
        occupants_by_house: dict[int, list[str]] = {h: [] for h in range(1, 13)}
        for p_name, p_lon in planet_positions.items():
            h_num = cls.get_house_for_longitude(p_lon, house_cusps)
            occupants_by_house[h_num].append(p_name)

        houses: list[WesternHouseInfo] = []
        for i in range(12):
            h_num = i + 1
            cusp = house_cusps[i] % 360.0
            sign_idx = int(cusp // 30)
            sign_enum = Sign(sign_idx)
            deg_in_sign = cusp % 30.0

            trad_ruler_enum = TRADITIONAL_RULERS[sign_enum]
            mod_ruler_enum = MODERN_RULERS[sign_enum]

            from app.config.constants import PLANET_NAMES

            trad_ruler_name = PLANET_NAMES.get(trad_ruler_enum, "Mars")
            mod_ruler_name = PLANET_NAMES.get(mod_ruler_enum, "Mars")

            houses.append(
                WesternHouseInfo(
                    house_number=h_num,
                    cusp_longitude=round(cusp, 4),
                    sign_index=sign_idx,
                    sign_name=SIGN_NAMES[sign_enum],
                    degree_in_sign=round(deg_in_sign, 4),
                    traditional_ruler=trad_ruler_name,
                    modern_ruler=mod_ruler_name,
                    occupants=sorted(occupants_by_house[h_num]),
                )
            )

        return houses
