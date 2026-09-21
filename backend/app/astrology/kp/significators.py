"""KP (Krishnamurti Paddhati) Significator theory engine.

Implements the 4-level KP significator chain that determines which houses
each planet signifies, and whether it gives positive or negative results.

Significator strength order (strongest → weakest):
1. Planets in the star (Nakshatra) of occupants of a house
2. Occupants of the house
3. Planets in the star of the lord of the house
4. Lord of the house

The sub-lord of each planet determines whether results are favourable or adverse.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from enum import IntEnum

from app.astrology.ephemeris import PlanetPosition
from app.astrology.kp.sublords import KpSubLordCalculator, KpSubLordInfo
from app.astrology.vedic.houses import VedicHouseInfo
from app.astrology.vedic.rashis import RashiCalculator


class KpSignificatorStrength(IntEnum):
    """Hierarchy of significator strength in KP (1 is strongest, 4 is weakest)."""

    LEVEL_1_STAR_OF_OCCUPANT = 1  # Planets in the star of an occupant (Strongest)
    LEVEL_2_OCCUPANT = 2          # Occupant of the house
    LEVEL_3_STAR_OF_LORD = 3      # Planets in the star of the house lord
    LEVEL_4_LORD = 4              # Lord of the house (Weakest)


@dataclass(frozen=True)
class KpHouseSignificators:
    """Significators for a single house across 4 KP levels."""

    house_number: int
    level_1_planets: list[str] = field(default_factory=list)  # In star of occupant
    level_2_planets: list[str] = field(default_factory=list)  # Occupants
    level_3_planets: list[str] = field(default_factory=list)  # In star of lord
    level_4_planets: list[str] = field(default_factory=list)  # House lord
    all_significators: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class KpPlanetSignification:
    """Full KP significator analysis for a single planet."""

    planet_name: str
    star_lord: str
    sub_lord: str
    sub_sub_lord: str
    kp_number: int
    # Houses signified at each level
    level_1_houses: list[int] = field(default_factory=list)  # Star of occupant
    level_2_houses: list[int] = field(default_factory=list)  # Direct occupant
    level_3_houses: list[int] = field(default_factory=list)  # Star of lord
    level_4_houses: list[int] = field(default_factory=list)  # Lordship
    # Combined result
    strong_houses: list[int] = field(default_factory=list)  # All signified houses (deduplicated)
    sub_lord_favourable_houses: list[int] = field(default_factory=list)
    sub_lord_unfavourable_houses: list[int] = field(default_factory=list)


class KpSignificatorEngine:
    """Computes 4-level KP significator chains for all planets.

    For each planet in the chart, determines which Bhava matters it signifies
    based on the KP 4-level hierarchy, and whether the sub-lord supports
    or obstructs each signification.
    """

    @classmethod
    def analyze_significators(
        cls,
        planets: list[PlanetPosition],
        bhavas: list[VedicHouseInfo],
        lagna_rashi_idx: int,
    ) -> dict[str, KpPlanetSignification]:
        """Compute full KP significator data for every planet.

        Args:
            planets: List of sidereal planetary positions.
            bhavas: Vedic bhava analysis (used for occupants and lords).
            lagna_rashi_idx: Lagna Rashi index (0=Aries).

        Returns:
            dict mapping planet name to its KpPlanetSignification.
        """
        # Build lookup structures
        # planet_name -> house it occupies
        planet_house_map: dict[str, int] = {}
        for bhava in bhavas:
            for occ in bhava.occupants:
                planet_house_map[occ] = bhava.house_number

        # house_number -> lord name
        house_lord_map: dict[int, str] = {}
        for bhava in bhavas:
            house_lord_map[bhava.house_number] = bhava.lord

        # house_number -> occupant names
        house_occupants: dict[int, list[str]] = {}
        for bhava in bhavas:
            house_occupants[bhava.house_number] = list(bhava.occupants)

        # planet_name -> star lord (Nakshatra ruler)
        planet_star_lords: dict[str, str] = {}
        planet_sublord_data: dict[str, KpSubLordInfo] = {}
        for p in planets:
            p_name = "Rahu" if p.name in ("North Node", "True Node") else p.name
            kp_info = KpSubLordCalculator.calculate_sublord(p.longitude)
            planet_star_lords[p_name] = kp_info.star_lord
            planet_sublord_data[p_name] = kp_info

        # For Ketu (if not in planets list, derived)
        rahu_pos = next((p for p in planets if p.name in ("North Node", "True Node")), None)
        if rahu_pos and "Ketu" not in planet_star_lords:
            ketu_lon = (rahu_pos.longitude + 180.0) % 360.0
            kp_info = KpSubLordCalculator.calculate_sublord(ketu_lon)
            planet_star_lords["Ketu"] = kp_info.star_lord
            planet_sublord_data["Ketu"] = kp_info

        # Build reverse: star_lord -> list of planets in that star
        star_to_planets: dict[str, list[str]] = {}
        for p_name, s_lord in planet_star_lords.items():
            star_to_planets.setdefault(s_lord, []).append(p_name)

        # Compute significators for each planet
        results: dict[str, KpPlanetSignification] = {}

        for p_name, kp_info in planet_sublord_data.items():
            level_1: list[int] = []
            level_2: list[int] = []
            level_3: list[int] = []
            level_4: list[int] = []

            # Level 2: Houses where this planet is an occupant
            if p_name in planet_house_map:
                level_2.append(planet_house_map[p_name])

            # Level 1: This planet's star lord is an occupant of which houses?
            # i.e., "planet is in the star of an occupant" — this planet signifies those houses
            star_lord = kp_info.star_lord
            if star_lord in planet_house_map:
                level_1.append(planet_house_map[star_lord])

            # Level 4: Houses this planet lords
            for h_num, lord in house_lord_map.items():
                if lord == p_name:
                    level_4.append(h_num)

            # Level 3: This planet is in the star of a house lord
            # The star lord rules which houses? Those houses are signified at level 3
            for h_num, lord in house_lord_map.items():
                if lord == star_lord:
                    level_3.append(h_num)

            # Deduplicate and combine
            all_houses = sorted(set(level_1 + level_2 + level_3 + level_4))

            # Sub-lord analysis: sub-lord's own significations determine favourable/unfavourable
            sub_lord = kp_info.sub_lord
            sub_favourable: list[int] = []
            sub_unfavourable: list[int] = []

            # Sub-lord favours houses it occupies and lords (simplified KP rule)
            if sub_lord in planet_house_map:
                sub_favourable.append(planet_house_map[sub_lord])
            for h_num, lord in house_lord_map.items():
                if lord == sub_lord:
                    sub_favourable.append(h_num)

            # Houses 6, 8, 12 from any signified house are unfavourable connections
            dusthana_offsets = {5, 7, 11}  # 6th, 8th, 12th from house (0-indexed)
            for h in all_houses:
                for offset in dusthana_offsets:
                    adverse_house = ((h - 1 + offset) % 12) + 1
                    if adverse_house in sub_favourable:
                        sub_unfavourable.append(h)

            results[p_name] = KpPlanetSignification(
                planet_name=p_name,
                star_lord=kp_info.star_lord,
                sub_lord=kp_info.sub_lord,
                sub_sub_lord=kp_info.sub_sub_lord,
                kp_number=KpSubLordCalculator.get_kp_number(
                    planet_sublord_data[p_name].nakshatra.index * (360.0 / 27.0)
                    + planet_sublord_data[p_name].nakshatra.longitude_in_nakshatra
                ),
                level_1_houses=sorted(set(level_1)),
                level_2_houses=sorted(set(level_2)),
                level_3_houses=sorted(set(level_3)),
                level_4_houses=sorted(set(level_4)),
                strong_houses=all_houses,
                sub_lord_favourable_houses=sorted(set(sub_favourable)),
                sub_lord_unfavourable_houses=sorted(set(sub_unfavourable)),
            )

        return results

    @classmethod
    def get_house_significators(
        cls,
        planet_significations: dict[str, KpPlanetSignification],
    ) -> dict[int, KpHouseSignificators]:
        """Invert planet significations to get significators for each of the 12 houses."""
        house_data: dict[int, dict[str, list[str]]] = {
            h: {"l1": [], "l2": [], "l3": [], "l4": []} for h in range(1, 13)
        }
        for p_name, sig in planet_significations.items():
            for h in sig.level_1_houses:
                if 1 <= h <= 12:
                    house_data[h]["l1"].append(p_name)
            for h in sig.level_2_houses:
                if 1 <= h <= 12:
                    house_data[h]["l2"].append(p_name)
            for h in sig.level_3_houses:
                if 1 <= h <= 12:
                    house_data[h]["l3"].append(p_name)
            for h in sig.level_4_houses:
                if 1 <= h <= 12:
                    house_data[h]["l4"].append(p_name)

        result: dict[int, KpHouseSignificators] = {}
        for h in range(1, 13):
            d = house_data[h]
            all_sigs = list(dict.fromkeys(d["l1"] + d["l2"] + d["l3"] + d["l4"]))
            result[h] = KpHouseSignificators(
                house_number=h,
                level_1_planets=sorted(set(d["l1"])),
                level_2_planets=sorted(set(d["l2"])),
                level_3_planets=sorted(set(d["l3"])),
                level_4_planets=sorted(set(d["l4"])),
                all_significators=all_sigs,
            )
        return result

