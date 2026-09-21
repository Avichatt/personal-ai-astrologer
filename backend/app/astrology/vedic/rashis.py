"""Vedic Sidereal signs (Rashis), lords, exaltation, debilitation, and Panchadha Maitri dignities."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class PlanetaryDignity(StrEnum):
    """Vedic planetary dignity classification."""

    EXALTED = "exalted"  # Uccha
    MOOLATRIKONA = "moolatrikona"  # Moolatrikona
    OWN_SIGN = "own_sign"  # Swa-kshetra
    GREAT_FRIEND = "great_friend"  # Adhi Mitra
    FRIEND = "friend"  # Mitra
    NEUTRAL = "neutral"  # Sama
    ENEMY = "enemy"  # Shatru
    GREAT_ENEMY = "great_enemy"  # Adhi Shatru
    DEBILITATED = "debilitated"  # Neecha


# Rashi Lordship (0 = Mesha .. 11 = Meena)
RASHI_LORDS: dict[int, str] = {
    0: "Mars",  # Mesha (Aries)
    1: "Venus",  # Vrishabha (Taurus)
    2: "Mercury",  # Mithuna (Gemini)
    3: "Moon",  # Karka (Cancer)
    4: "Sun",  # Simha (Leo)
    5: "Mercury",  # Kanya (Virgo)
    6: "Venus",  # Tula (Libra)
    7: "Mars",  # Vrishchika (Scorpio)
    8: "Jupiter",  # Dhanu (Sagittarius)
    9: "Saturn",  # Makara (Capricorn)
    10: "Saturn",  # Kumbha (Aquarius)
    11: "Jupiter",  # Meena (Pisces)
}

# Exaltation and Debilitation Signs (Sign index and exact deep degree)
EXALTATION_MAP: dict[str, tuple[int, float]] = {
    "Sun": (0, 10.0),  # Aries 10°
    "Moon": (1, 3.0),  # Taurus 3°
    "Mars": (9, 28.0),  # Capricorn 28°
    "Mercury": (5, 15.0),  # Virgo 15°
    "Jupiter": (3, 5.0),  # Cancer 5°
    "Venus": (11, 27.0),  # Pisces 27°
    "Saturn": (6, 20.0),  # Libra 20°
    "North Node": (1, 20.0),  # Taurus / Gemini
    "Rahu": (1, 20.0),
    "Ketu": (7, 20.0),  # Scorpio / Sagittarius
}

DEBILITATION_MAP: dict[str, tuple[int, float]] = {
    "Sun": (6, 10.0),  # Libra 10°
    "Moon": (7, 3.0),  # Scorpio 3°
    "Mars": (3, 28.0),  # Cancer 28°
    "Mercury": (11, 15.0),  # Pisces 15°
    "Jupiter": (9, 5.0),  # Capricorn 5°
    "Venus": (5, 27.0),  # Virgo 27°
    "Saturn": (0, 20.0),  # Aries 20°
    "North Node": (7, 20.0),  # Scorpio
    "Rahu": (7, 20.0),
    "Ketu": (1, 20.0),  # Taurus
}

# Moolatrikona zones: sign_idx, start_deg, end_deg
MOOLATRIKONA_MAP: dict[str, tuple[int, float, float]] = {
    "Sun": (4, 0.0, 20.0),  # Leo 0°-20°
    "Moon": (1, 3.0, 30.0),  # Taurus 3°-30°
    "Mars": (0, 0.0, 12.0),  # Aries 0°-12°
    "Mercury": (5, 15.0, 20.0),  # Virgo 15°-20°
    "Jupiter": (8, 0.0, 10.0),  # Sagittarius 0°-10°
    "Venus": (6, 0.0, 15.0),  # Libra 0°-15°
    "Saturn": (10, 0.0, 20.0),  # Aquarius 0°-20°
}

# Natural Relationships (Naisargika Maitri): 1 = Friend, 0 = Neutral, -1 = Enemy
NATURAL_RELATIONS: dict[str, dict[str, int]] = {
    "Sun": {"Moon": 1, "Mars": 1, "Jupiter": 1, "Mercury": 0, "Venus": -1, "Saturn": -1},
    "Moon": {"Sun": 1, "Mercury": 1, "Mars": 0, "Jupiter": 0, "Venus": 0, "Saturn": 0},
    "Mars": {"Sun": 1, "Moon": 1, "Jupiter": 1, "Venus": 0, "Saturn": 0, "Mercury": -1},
    "Mercury": {"Sun": 1, "Venus": 1, "Mars": 0, "Jupiter": 0, "Saturn": 0, "Moon": -1},
    "Jupiter": {"Sun": 1, "Moon": 1, "Mars": 1, "Saturn": 0, "Mercury": -1, "Venus": -1},
    "Venus": {"Mercury": 1, "Saturn": 1, "Mars": 0, "Jupiter": 0, "Sun": -1, "Moon": -1},
    "Saturn": {"Mercury": 1, "Venus": 1, "Jupiter": 0, "Sun": -1, "Moon": -1, "Mars": -1},
}


@dataclass(frozen=True)
class RashiInfo:
    """Detailed Vedic Rashi placement for a planet."""

    planet_name: str
    rashi_index: int  # 0 = Mesha .. 11 = Meena
    rashi_name: str  # e.g. "Mesha", "Vrishabha"
    longitude_in_rashi: float
    rashi_lord: str
    dignity: PlanetaryDignity
    is_vargottama: bool  # Same sign in D1 (Rashi) and D9 (Navamsha)


class RashiCalculator:
    """Calculates Vedic Sidereal sign attributes, lordships, and Panchadha Maitri."""

    @classmethod
    def get_rashi_lord(cls, rashi_index: int) -> str:
        """Get the ruling Graha for a rashi."""
        return RASHI_LORDS.get(rashi_index % 12, "Mars")

    @classmethod
    def calculate_panchadha_maitri(
        cls,
        planet: str,
        sign_lord: str,
        planet_sign_idx: int,
        lord_sign_idx: int,
    ) -> PlanetaryDignity:
        """
        Calculate 5-fold relationship (Panchadha Maitri) between planet and sign lord.
        """
        if planet == sign_lord:
            return PlanetaryDignity.OWN_SIGN

        # 1. Natural Relation
        nat_score = NATURAL_RELATIONS.get(planet, {}).get(sign_lord, 0)

        # 2. Temporal Relation (Tatkalika): 2, 3, 4, 10, 11, 12 from planet = Friend (+1), else Enemy (-1)
        dist = (lord_sign_idx - planet_sign_idx) % 12
        tat_score = 1 if dist in (1, 2, 3, 9, 10, 11) else -1

        composite = nat_score + tat_score

        if composite >= 2:
            return PlanetaryDignity.GREAT_FRIEND
        elif composite == 1:
            return PlanetaryDignity.FRIEND
        elif composite == 0:
            return PlanetaryDignity.NEUTRAL
        elif composite == -1:
            return PlanetaryDignity.ENEMY
        else:
            return PlanetaryDignity.GREAT_ENEMY

    @classmethod
    def evaluate_dignity(
        cls,
        planet_name: str,
        sign_index: int,
        degree_in_sign: float,
        lord_sign_index: int | None = None,
    ) -> PlanetaryDignity:
        """
        Determine comprehensive dignity of a planet (Exalted, Debilitated, Moolatrikona, Own Sign, or Maitri).
        """
        # Check Exaltation
        if planet_name in EXALTATION_MAP:
            ex_sign, _ = EXALTATION_MAP[planet_name]
            if sign_index == ex_sign:
                return PlanetaryDignity.EXALTED

        # Check Debilitation
        if planet_name in DEBILITATION_MAP:
            deb_sign, _ = DEBILITATION_MAP[planet_name]
            if sign_index == deb_sign:
                return PlanetaryDignity.DEBILITATED

        # Check Moolatrikona
        if planet_name in MOOLATRIKONA_MAP:
            m_sign, start_deg, end_deg = MOOLATRIKONA_MAP[planet_name]
            if sign_index == m_sign and start_deg <= degree_in_sign < end_deg:
                return PlanetaryDignity.MOOLATRIKONA

        sign_lord = cls.get_rashi_lord(sign_index)
        if planet_name == sign_lord:
            return PlanetaryDignity.OWN_SIGN

        # Panchadha Maitri with sign lord
        lord_sign = lord_sign_index if lord_sign_index is not None else sign_index
        return cls.calculate_panchadha_maitri(
            planet=planet_name,
            sign_lord=sign_lord,
            planet_sign_idx=sign_index,
            lord_sign_idx=lord_sign,
        )
