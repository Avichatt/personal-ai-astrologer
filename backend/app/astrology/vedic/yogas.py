"""Vedic Yoga and Dosha detection engine (Raja, Dhana, Mahapurusha, Gajakesari, Manglik, etc.)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.astrology.ephemeris import PlanetPosition
from app.astrology.vedic.houses import KENDRAS, TRIKONAS, VedicHouseCalculator, VedicHouseInfo
from app.astrology.vedic.rashis import PlanetaryDignity


class YogaCategory(StrEnum):
    RAJA_YOGA = "raja_yoga"
    DHANA_YOGA = "dhana_yoga"
    MAHAPURUSHA_YOGA = "mahapurusha_yoga"
    AUSPICIOUS = "auspicious"
    INAUSPICIOUS = "inauspicious"
    DOSHA = "dosha"


@dataclass(frozen=True)
class VedicYogaResult:
    """Detected Vedic Yoga or Dosha configuration."""

    name: str
    category: YogaCategory
    participating_planets: list[str]
    houses_involved: list[int]
    description: str
    strength: str  # "High", "Medium", "Mild"


class VedicYogaEngine:
    """Detects Classical Parashari and Jaimini Yogas in a Vedic natal chart."""

    @classmethod
    def detect_yogas(
        cls,
        lagna_longitude: float,
        planets: list[PlanetPosition],
        bhavas: list[VedicHouseInfo],
        dignities: dict[str, PlanetaryDignity],
    ) -> list[VedicYogaResult]:
        """
        Evaluate all classical yogas and doshas present in the chart.
        """
        yogas: list[VedicYogaResult] = []
        lagna_rashi_idx = int(lagna_longitude // 30) % 12

        # Map planet name -> house number & sign index
        p_house_map: dict[str, int] = {}
        p_sign_map: dict[str, int] = {}
        for p in planets:
            p_name = "Rahu" if p.name in ("North Node", "True Node") else p.name
            sign_idx = int(p.longitude // 30) % 12
            h_num = VedicHouseCalculator.get_house_for_rashi(sign_idx, lagna_rashi_idx)
            p_house_map[p_name] = h_num
            p_sign_map[p_name] = sign_idx

        # Map house number -> lord name
        house_lords: dict[int, str] = {bh.house_number: bh.lord for bh in bhavas}

        # 1. Pancha Mahapurusha Yogas
        # Mars=Ruchaka, Mercury=Bhadra, Jupiter=Hamsa, Venus=Malavya, Saturn=Sasa
        mahapurusha_defs = [
            (
                "Mars",
                "Ruchaka Yoga",
                "Courage, leadership, military/executive prowess, physical vitality",
            ),
            (
                "Mercury",
                "Bhadra Yoga",
                "High intellect, eloquence, sharp memory, commercial success",
            ),
            ("Jupiter", "Hamsa Yoga", "Wisdom, virtue, spiritual inclination, widespread respect"),
            ("Venus", "Malavya Yoga", "Beauty, luxury, artistic mastery, wealth, sensual joy"),
            ("Saturn", "Sasa Yoga", "Authority over masses, discipline, endurance, longevity"),
        ]

        for p_name, yoga_name, desc in mahapurusha_defs:
            if p_name in p_house_map:
                h_num = p_house_map[p_name]
                dignity = dignities.get(p_name, PlanetaryDignity.NEUTRAL)
                if h_num in KENDRAS and dignity in (
                    PlanetaryDignity.EXALTED,
                    PlanetaryDignity.OWN_SIGN,
                    PlanetaryDignity.MOOLATRIKONA,
                ):
                    yogas.append(
                        VedicYogaResult(
                            name=yoga_name,
                            category=YogaCategory.MAHAPURUSHA_YOGA,
                            participating_planets=[p_name],
                            houses_involved=[h_num],
                            description=f"{p_name} placed in Kendra (House {h_num}) in strong dignity creates {yoga_name}. {desc}.",
                            strength="High",
                        )
                    )

        # 2. Gajakesari Yoga (Jupiter in Kendra from Moon: 1, 4, 7, 10)
        if "Jupiter" in p_house_map and "Moon" in p_house_map:
            jup_h = p_house_map["Jupiter"]
            moon_h = p_house_map["Moon"]
            diff = ((jup_h - moon_h) % 12) + 1
            if diff in KENDRAS:
                yogas.append(
                    VedicYogaResult(
                        name="Gajakesari Yoga",
                        category=YogaCategory.AUSPICIOUS,
                        participating_planets=["Jupiter", "Moon"],
                        houses_involved=[moon_h, jup_h],
                        description="Jupiter is in a Kendra from the Moon, conferring wisdom, enduring fame, and honorable status.",
                        strength="High",
                    )
                )

        # 3. Budhaditya Yoga (Sun + Mercury in same rashi)
        if (
            "Sun" in p_sign_map
            and "Mercury" in p_sign_map
            and p_sign_map["Sun"] == p_sign_map["Mercury"]
        ):
            h_num = p_house_map["Sun"]
            yogas.append(
                VedicYogaResult(
                    name="Budhaditya Yoga",
                    category=YogaCategory.AUSPICIOUS,
                    participating_planets=["Sun", "Mercury"],
                    houses_involved=[h_num],
                    description=f"Conjunction of Sun and Mercury in House {h_num} bestows intellectual brilliance and administrative skill.",
                    strength="Medium",
                )
            )

        # 4. Chandra-Mangala Yoga (Moon + Mars in same rashi or mutual kendras)
        if (
            "Moon" in p_sign_map
            and "Mars" in p_sign_map
            and p_sign_map["Moon"] == p_sign_map["Mars"]
        ):
            h_num = p_house_map["Moon"]
            yogas.append(
                VedicYogaResult(
                    name="Chandra-Mangala Yoga",
                    category=YogaCategory.DHANA_YOGA,
                    participating_planets=["Moon", "Mars"],
                    houses_involved=[h_num],
                    description="Conjunction of Moon and Mars in the same sign provides strong financial drive and enterprise.",
                    strength="Medium",
                )
            )

        # 5. Raja Yogas: Kendra lord + Trikona lord conjunction
        kendra_lords = {house_lords[h] for h in KENDRAS}
        trikona_lords = {house_lords[h] for h in TRIKONAS}

        for k_lord in kendra_lords:
            for t_lord in trikona_lords:
                if (
                    k_lord != t_lord
                    and k_lord in p_sign_map
                    and t_lord in p_sign_map
                    and p_sign_map[k_lord] == p_sign_map[t_lord]
                ):
                    h_num = p_house_map[k_lord]
                    yogas.append(
                        VedicYogaResult(
                            name=f"Raja Yoga ({k_lord} + {t_lord})",
                            category=YogaCategory.RAJA_YOGA,
                            participating_planets=[k_lord, t_lord],
                            houses_involved=[h_num],
                            description=f"Kendra lord {k_lord} conjunct Trikona lord {t_lord} in House {h_num} elevates social rank, authority, and prosperity.",
                            strength="High",
                        )
                    )

        # 6. Vipreet Raja Yogas (Lords of 6, 8, 12 placed in 6, 8, or 12)
        dusthana_houses = {6, 8, 12}
        l6, l8, l12 = house_lords[6], house_lords[8], house_lords[12]

        if l6 in p_house_map and p_house_map[l6] in dusthana_houses:
            yogas.append(
                VedicYogaResult(
                    name="Harsha Yoga (Vipreet Raja)",
                    category=YogaCategory.RAJA_YOGA,
                    participating_planets=[l6],
                    houses_involved=[p_house_map[l6]],
                    description="6th Lord placed in a Dusthana grants invincibility against adversaries, good health, and success after struggle.",
                    strength="Medium",
                )
            )

        if l8 in p_house_map and p_house_map[l8] in dusthana_houses:
            yogas.append(
                VedicYogaResult(
                    name="Sarala Yoga (Vipreet Raja)",
                    category=YogaCategory.RAJA_YOGA,
                    participating_planets=[l8],
                    houses_involved=[p_house_map[l8]],
                    description="8th Lord placed in a Dusthana grants longevity, fearlessness, sudden wealth, and resilience in crises.",
                    strength="Medium",
                )
            )

        if l12 in p_house_map and p_house_map[l12] in dusthana_houses:
            yogas.append(
                VedicYogaResult(
                    name="Vimala Yoga (Vipreet Raja)",
                    category=YogaCategory.RAJA_YOGA,
                    participating_planets=[l12],
                    houses_involved=[p_house_map[l12]],
                    description="12th Lord placed in a Dusthana promotes independent wealth, spiritual purity, and contentment.",
                    strength="Medium",
                )
            )

        # 7. Guru Chandal Yoga (Jupiter conjunct Rahu or Ketu)
        if "Jupiter" in p_sign_map:
            jup_sign = p_sign_map["Jupiter"]
            if ("Rahu" in p_sign_map and p_sign_map["Rahu"] == jup_sign) or (
                "Ketu" in p_sign_map and p_sign_map["Ketu"] == jup_sign
            ):
                node = (
                    "Rahu" if ("Rahu" in p_sign_map and p_sign_map["Rahu"] == jup_sign) else "Ketu"
                )
                yogas.append(
                    VedicYogaResult(
                        name="Guru Chandal Yoga",
                        category=YogaCategory.DOSHA,
                        participating_planets=["Jupiter", node],
                        houses_involved=[p_house_map["Jupiter"]],
                        description=f"Conjunction of Jupiter with {node} creates unconventional beliefs, philosophical questioning, or mentorship challenges.",
                        strength="Medium",
                    )
                )

        # 8. Manglik / Kuja Dosha (Mars in 1st, 2nd, 4th, 7th, 8th, or 12th from Lagna)
        manglik_houses = {1, 2, 4, 7, 8, 12}
        if "Mars" in p_house_map:
            mars_h = p_house_map["Mars"]
            if mars_h in manglik_houses:
                yogas.append(
                    VedicYogaResult(
                        name="Manglik Dosha (Kuja Dosha)",
                        category=YogaCategory.DOSHA,
                        participating_planets=["Mars"],
                        houses_involved=[mars_h],
                        description=f"Mars placed in House {mars_h} activates passionate energy and dynamic relationship dynamics requiring conscious balance.",
                        strength="Medium",
                    )
                )

        return yogas
