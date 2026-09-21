"""Vedic Bhavas (Houses), Jaimini Chara Karakas, and Parashara Drishti aspect engine."""

from __future__ import annotations

from dataclasses import dataclass

from app.astrology.ephemeris import PlanetPosition
from app.astrology.vedic.rashis import RashiCalculator
from app.config.constants import RASHI_NAMES, Sign

# House Categories
KENDRAS = {1, 4, 7, 10}
TRIKONAS = {1, 5, 9}
DUSTHANAS = {6, 8, 12}
UPACHAYAS = {3, 6, 10, 11}
MARAKAS = {2, 7}


@dataclass(frozen=True)
class VedicHouseInfo:
    """Detailed Vedic Bhava representation."""

    house_number: int  # 1 through 12
    rashi_index: int  # 0 = Mesha .. 11 = Meena
    rashi_name: str
    cusp_longitude: float  # In whole-sign / equal-house Vedic system
    lord: str  # Ruling graha
    is_kendra: bool
    is_trikona: bool
    is_dusthana: bool
    is_upachaya: bool
    is_maraka: bool
    occupants: list[str]  # Grahas occupying this bhava
    aspecting_grahas: list[str]  # Grahas casting Parashara drishti on this bhava


@dataclass(frozen=True)
class CharaKaraka:
    """Jaimini Chara Karaka designation."""

    code: str  # AK, AmK, BK, MK, PiK, PK, GK, DK
    title: str  # Atmakaraka, Amatyakaraka, etc.
    planet_name: str
    sign_name: str
    degree_in_sign: float


class VedicHouseCalculator:
    """Calculates Vedic Bhavas, House Lords, Jaimini Karakas, and Drishti (aspects)."""

    @classmethod
    def get_house_for_rashi(cls, rashi_idx: int, lagna_rashi_idx: int) -> int:
        """Calculate house number (1-12) from Lagna rashi using Whole Sign system."""
        return ((rashi_idx - lagna_rashi_idx) % 12) + 1

    @classmethod
    def calculate_jaimini_karakas(cls, planets: list[PlanetPosition]) -> list[CharaKaraka]:
        """
        Compute 8 Jaimini Chara Karakas based on descending degree within the rashi.
        Eligible bodies: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu.
        """
        eligible_names = {
            "Sun",
            "Moon",
            "Mars",
            "Mercury",
            "Jupiter",
            "Venus",
            "Saturn",
            "North Node",
            "Rahu",
        }
        eligible_planets = [p for p in planets if p.name in eligible_names]

        # Standardize Rahu name
        cleaned: list[tuple[str, str, float]] = []
        for p in eligible_planets:
            p_name = "Rahu" if p.name in ("North Node", "True Node") else p.name
            deg_in_sign = p.sign_longitude
            cleaned.append((p_name, p.sign_name, deg_in_sign))

        # Sort descending by degree in sign
        cleaned.sort(key=lambda item: item[2], reverse=True)

        karaka_defs = [
            ("AK", "Atmakaraka (Soul Significator)"),
            ("AmK", "Amatyakaraka (Career & Mind)"),
            ("BK", "Bhratrukaraka (Siblings & Guru)"),
            ("MK", "Matrukaraka (Mother & Emotion)"),
            ("PiK", "Pitrukaraka (Father & Ancestry)"),
            ("PK", "Putrakaraka (Children & Intellect)"),
            ("GK", "Gnatikaraka (Obstacles & Competition)"),
            ("DK", "Darakaraka (Spouse & Partner)"),
        ]

        results: list[CharaKaraka] = []
        for i in range(min(len(cleaned), len(karaka_defs))):
            code, title = karaka_defs[i]
            p_name, sign_name, deg = cleaned[i]
            results.append(
                CharaKaraka(
                    code=code,
                    title=title,
                    planet_name=p_name,
                    sign_name=sign_name,
                    degree_in_sign=round(deg, 4),
                )
            )

        return results

    @classmethod
    def calculate_parashara_drishti(
        cls,
        planet_name: str,
        planet_house: int,
    ) -> list[int]:
        """
        Calculate houses aspected by a planet using Parashara rules.
        """
        # All planets cast full 7th aspect
        aspects = [((planet_house - 1 + 6) % 12) + 1]

        # Mars: 4th, 7th, 8th
        if planet_name in ("Mars", "Mangal"):
            aspects.append(((planet_house - 1 + 3) % 12) + 1)
            aspects.append(((planet_house - 1 + 7) % 12) + 1)

        # Jupiter, Rahu, Ketu: 5th, 7th, 9th
        elif planet_name in ("Jupiter", "Guru", "Rahu", "North Node", "Ketu"):
            aspects.append(((planet_house - 1 + 4) % 12) + 1)
            aspects.append(((planet_house - 1 + 8) % 12) + 1)

        # Saturn: 3rd, 7th, 10th
        elif planet_name in ("Saturn", "Shani"):
            aspects.append(((planet_house - 1 + 2) % 12) + 1)
            aspects.append(((planet_house - 1 + 9) % 12) + 1)

        return sorted(list(set(aspects)))

    @classmethod
    def analyze_bhavas(
        cls,
        lagna_longitude: float,
        planets: list[PlanetPosition],
    ) -> list[VedicHouseInfo]:
        """
        Compute full analysis for all 12 Vedic Bhavas from the Sidereal Ascendant (Lagna).
        """
        lagna_rashi_idx = int(lagna_longitude // 30) % 12

        # Map planet to its house from Lagna
        planet_house_map: dict[str, int] = {}
        occupants_by_house: dict[int, list[str]] = {h: [] for h in range(1, 13)}

        for p in planets:
            p_rashi_idx = int(p.longitude // 30) % 12
            h_num = cls.get_house_for_rashi(p_rashi_idx, lagna_rashi_idx)
            p_name = "Rahu" if p.name in ("North Node", "True Node") else p.name
            planet_house_map[p_name] = h_num
            occupants_by_house[h_num].append(p_name)

        # Map drishti aspects hitting each house
        aspects_hitting_house: dict[int, list[str]] = {h: [] for h in range(1, 13)}
        for p_name, h_num in planet_house_map.items():
            aspected_houses = cls.calculate_parashara_drishti(p_name, h_num)
            for ah in aspected_houses:
                aspects_hitting_house[ah].append(p_name)

        bhavas: list[VedicHouseInfo] = []
        for h in range(1, 13):
            rashi_idx = (lagna_rashi_idx + (h - 1)) % 12
            rashi_sign = Sign(rashi_idx)
            rashi_name = RASHI_NAMES[rashi_sign]
            lord = RashiCalculator.get_rashi_lord(rashi_idx)
            cusp_lon = rashi_idx * 30.0

            bhavas.append(
                VedicHouseInfo(
                    house_number=h,
                    rashi_index=rashi_idx,
                    rashi_name=rashi_name,
                    cusp_longitude=round(cusp_lon, 4),
                    lord=lord,
                    is_kendra=h in KENDRAS,
                    is_trikona=h in TRIKONAS,
                    is_dusthana=h in DUSTHANAS,
                    is_upachaya=h in UPACHAYAS,
                    is_maraka=h in MARAKAS,
                    occupants=sorted(occupants_by_house[h]),
                    aspecting_grahas=sorted(aspects_hitting_house[h]),
                )
            )

        return bhavas
