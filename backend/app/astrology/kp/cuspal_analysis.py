"""KP cuspal sub-lord analysis.

In KP, the sub-lord of each Placidus house cusp determines whether the house
promise is fulfilled. This module analyzes all 12 cusps to determine their
KP sub-lord chain and house significations.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.astrology.kp.sublords import KpSubLordCalculator, KpSubLordInfo
from app.astrology.vedic.rashis import RashiCalculator
from app.config.constants import RASHI_NAMES


@dataclass(frozen=True)
class KpCuspInfo:
    """KP analysis for a single Placidus house cusp."""

    cusp_number: int  # 1-12
    longitude: float  # Sidereal longitude of the cusp
    sign_lord: str
    star_lord: str
    sub_lord: str
    sub_sub_lord: str
    kp_number: int
    rashi_name: str = ""
    # Sub-lord's own house significations (determines if house promise is fulfilled)
    sub_lord_signifies_houses: list[int] = field(default_factory=list)
    # Whether the sub-lord supports the house matters (simplified assessment)
    is_promise_positive: bool = True


# Houses whose sub-lord signification supports the cusp's own house promise
# For KP analysis, the sub-lord must signify the house itself or supporting houses
# to give positive results. Supporting houses are defined per matter.
KP_HOUSE_MATTERS: dict[int, dict[str, list[int]]] = {
    1: {"matter": "Self, Health, Personality", "supporting": [1, 5, 9, 11], "opposing": [6, 8, 12]},
    2: {"matter": "Wealth, Family, Speech", "supporting": [2, 6, 10, 11], "opposing": [1, 8, 12]},
    3: {"matter": "Siblings, Courage, Short Travel", "supporting": [3, 9, 11], "opposing": [5, 8, 12]},
    4: {"matter": "Mother, Property, Education", "supporting": [4, 11, 12], "opposing": [3, 5, 10]},
    5: {"matter": "Children, Intelligence, Creativity", "supporting": [2, 5, 11], "opposing": [1, 4, 10]},
    6: {"matter": "Enemies, Disease, Service", "supporting": [1, 6, 10, 11], "opposing": [5, 7, 12]},
    7: {"matter": "Marriage, Partnership, Business", "supporting": [2, 7, 11], "opposing": [1, 6, 10]},
    8: {"matter": "Longevity, Transformation, Inheritance", "supporting": [8, 11, 12], "opposing": [1, 6, 10]},
    9: {"matter": "Fortune, Guru, Higher Learning", "supporting": [5, 9, 11], "opposing": [3, 6, 8]},
    10: {"matter": "Career, Status, Authority", "supporting": [2, 6, 10, 11], "opposing": [1, 5, 12]},
    11: {"matter": "Gains, Income, Aspirations", "supporting": [3, 6, 11], "opposing": [5, 8, 12]},
    12: {"matter": "Loss, Moksha, Foreign Travel", "supporting": [3, 9, 12], "opposing": [1, 6, 10]},
}


class KpCuspalAnalysis:
    """Analyzes all 12 Placidus cusps using KP sub-lord theory."""

    @classmethod
    def analyze_cusps(
        cls,
        placidus_cusps: list[float],
        ayanamsa_value: float,
        planet_house_map: dict[str, int] | None = None,
        house_lord_map: dict[int, str] | None = None,
    ) -> list[KpCuspInfo]:
        """Analyze all 12 cusps for their KP sub-lord chain.

        Args:
            placidus_cusps: 12 Placidus cusp longitudes (tropical).
            ayanamsa_value: Ayanamsa to convert to sidereal.
            planet_house_map: Optional mapping of planet name to house for sub-lord assessment.
            house_lord_map: Optional mapping of house number to lord name.

        Returns:
            List of 12 KpCuspInfo objects.
        """
        results: list[KpCuspInfo] = []

        for i, cusp_lon in enumerate(placidus_cusps):
            cusp_num = i + 1
            # Convert tropical cusp to sidereal
            sidereal_cusp = (cusp_lon - ayanamsa_value) % 360.0

            kp_info: KpSubLordInfo = KpSubLordCalculator.calculate_sublord(sidereal_cusp)
            kp_number = KpSubLordCalculator.get_kp_number(sidereal_cusp)

            # Determine sub-lord's house significations (if mappings provided)
            sub_lord_houses: list[int] = []
            is_positive = True

            if planet_house_map and house_lord_map:
                sub_lord = kp_info.sub_lord

                # Sub-lord occupies which house?
                if sub_lord in planet_house_map:
                    sub_lord_houses.append(planet_house_map[sub_lord])

                # Sub-lord lords which houses?
                for h_num, lord in house_lord_map.items():
                    if lord == sub_lord:
                        sub_lord_houses.append(h_num)

                sub_lord_houses = sorted(set(sub_lord_houses))

                # Check if sub-lord supports the cusp's house matters
                house_config = KP_HOUSE_MATTERS.get(cusp_num, {})
                supporting = house_config.get("supporting", [])
                opposing = house_config.get("opposing", [])

                support_score = sum(1 for h in sub_lord_houses if h in supporting)
                oppose_score = sum(1 for h in sub_lord_houses if h in opposing)
                is_positive = support_score >= oppose_score

            rashi_idx = int(sidereal_cusp // 30) % 12
            sign_lord = RashiCalculator.get_rashi_lord(rashi_idx)
            rashi_name = RASHI_NAMES.get(rashi_idx, "Aries")

            results.append(
                KpCuspInfo(
                    cusp_number=cusp_num,
                    longitude=round(sidereal_cusp, 6),
                    sign_lord=sign_lord,
                    star_lord=kp_info.star_lord,
                    sub_lord=kp_info.sub_lord,
                    sub_sub_lord=kp_info.sub_sub_lord,
                    kp_number=kp_number,
                    rashi_name=rashi_name,
                    sub_lord_signifies_houses=sub_lord_houses,
                    is_promise_positive=is_positive,
                )
            )

        return results
