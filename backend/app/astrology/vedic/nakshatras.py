"""Vedic 27 Nakshatras and 108 Padas calculations."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.config.constants import NAKSHATRA_NAMES, NAKSHATRA_SPAN_DEGREES, Nakshatra


class Gana(StrEnum):
    DEVA = "deva"
    MANUSHYA = "manushya"
    RAKSHASA = "rakshasa"


class Nadi(StrEnum):
    ADI = "adi"  # Vata
    MADHYA = "madhya"  # Pitta
    ANTYA = "antya"  # Kapha


# Nakshatra Attributes: (Gana, Nadi, Yoni, Tattva, Deity, Vimshottari Ruler)
NAKSHATRA_METADATA: dict[int, tuple[Gana, Nadi, str, str, str, str]] = {
    0: (Gana.DEVA, Nadi.ADI, "Horse", "Fire", "Ashwini Kumaras", "Ketu"),
    1: (Gana.MANUSHYA, Nadi.MADHYA, "Elephant", "Earth", "Yama", "Venus"),
    2: (Gana.RAKSHASA, Nadi.ANTYA, "Sheep", "Fire", "Agni", "Sun"),
    3: (Gana.MANUSHYA, Nadi.ANTYA, "Serpent", "Earth", "Brahma / Prajapati", "Moon"),
    4: (Gana.DEVA, Nadi.MADHYA, "Serpent", "Earth", "Soma (Chandra)", "Mars"),
    5: (Gana.MANUSHYA, Nadi.ADI, "Dog", "Water", "Rudra (Shiva)", "Rahu"),
    6: (Gana.DEVA, Nadi.ADI, "Cat", "Air", "Aditi", "Jupiter"),
    7: (Gana.DEVA, Nadi.MADHYA, "Goat", "Water", "Brihaspati", "Saturn"),
    8: (Gana.RAKSHASA, Nadi.ANTYA, "Cat", "Water", "Sarpas (Nagas)", "Mercury"),
    9: (Gana.RAKSHASA, Nadi.ANTYA, "Rat", "Fire", "Pitris (Ancestors)", "Ketu"),
    10: (Gana.MANUSHYA, Nadi.MADHYA, "Rat", "Fire", "Bhaga", "Venus"),
    11: (Gana.MANUSHYA, Nadi.ADI, "Cow", "Fire", "Aryaman", "Sun"),
    12: (Gana.DEVA, Nadi.ADI, "Buffalo", "Earth", "Savitur (Surya)", "Moon"),
    13: (Gana.RAKSHASA, Nadi.MADHYA, "Tiger", "Air", "Tvashtr (Vishwakarma)", "Mars"),
    14: (Gana.DEVA, Nadi.ANTYA, "Buffalo", "Air", "Vayu", "Rahu"),
    15: (Gana.RAKSHASA, Nadi.ANTYA, "Tiger", "Fire", "Indra-Agni", "Jupiter"),
    16: (Gana.DEVA, Nadi.MADHYA, "Deer", "Water", "Mitra", "Saturn"),
    17: (Gana.RAKSHASA, Nadi.ADI, "Deer", "Water", "Indra", "Mercury"),
    18: (Gana.RAKSHASA, Nadi.ADI, "Dog", "Air", "Nirriti", "Ketu"),
    19: (Gana.MANUSHYA, Nadi.MADHYA, "Monkey", "Water", "Apah (Water)", "Venus"),
    20: (Gana.MANUSHYA, Nadi.ANTYA, "Mongoose", "Earth", "Vishvedevas", "Sun"),
    21: (Gana.DEVA, Nadi.ANTYA, "Monkey", "Air", "Vishnu", "Moon"),
    22: (Gana.RAKSHASA, Nadi.MADHYA, "Lion", "Air", "Eight Vasus", "Mars"),
    23: (Gana.RAKSHASA, Nadi.ADI, "Horse", "Ether", "Varuna", "Rahu"),
    24: (Gana.MANUSHYA, Nadi.ADI, "Lion", "Ether", "Aja Ekapada", "Jupiter"),
    25: (Gana.MANUSHYA, Nadi.MADHYA, "Cow", "Water", "Ahirbudhnya", "Saturn"),
    26: (Gana.DEVA, Nadi.ANTYA, "Elephant", "Water", "Pushan", "Mercury"),
}

PADA_SPAN_DEGREES: float = NAKSHATRA_SPAN_DEGREES / 4.0  # 3°20' = 3.3333333°


@dataclass(frozen=True)
class NakshatraInfo:
    """Detailed Nakshatra and Pada position."""

    index: int  # 0 = Ashwini .. 26 = Revati
    name: str
    pada: int  # 1, 2, 3, or 4
    total_pada_index: int  # 0 to 107 across the zodiac
    longitude_in_nakshatra: float
    longitude_in_pada: float
    elapsed_fraction: float  # [0.0, 1.0] fraction of nakshatra traversed
    ruler: str  # Vimshottari dasha lord
    navamsha_sign_index: int  # D9 sign (0=Aries .. 11=Pisces)
    navamsha_sign_name: str
    gana: Gana
    nadi: Nadi
    yoni: str
    tattva: str
    deity: str


class NakshatraCalculator:
    """Calculates Nakshatra, Pada, Navamsha sign, and astrological attributes from sidereal longitude."""

    @classmethod
    def calculate_from_longitude(cls, sidereal_longitude: float) -> NakshatraInfo:
        """
        Compute full Nakshatra & Pada information for a given sidereal longitude [0, 360).
        """
        lon = sidereal_longitude % 360.0

        nak_idx = int(lon // NAKSHATRA_SPAN_DEGREES)
        nak_idx = min(nak_idx, 26)  # Guard against boundary

        nak_enum = Nakshatra(nak_idx)
        nak_name = NAKSHATRA_NAMES[nak_enum]

        deg_in_nak = lon - (nak_idx * NAKSHATRA_SPAN_DEGREES)
        elapsed_frac = deg_in_nak / NAKSHATRA_SPAN_DEGREES

        pada = int(deg_in_nak // PADA_SPAN_DEGREES) + 1
        pada = min(pada, 4)

        deg_in_pada = deg_in_nak - ((pada - 1) * PADA_SPAN_DEGREES)

        total_pada_idx = (nak_idx * 4) + (pada - 1)  # 0 to 107

        # Navamsha sign (D9) cycles 0 to 11 starting from Aries (0) for each pada
        nav_sign_idx = total_pada_idx % 12
        from app.config.constants import RASHI_NAMES, Sign

        nav_sign_name = RASHI_NAMES[Sign(nav_sign_idx)]

        meta = NAKSHATRA_METADATA.get(
            nak_idx, (Gana.DEVA, Nadi.ADI, "Horse", "Fire", "Divine", "Ketu")
        )

        return NakshatraInfo(
            index=nak_idx,
            name=nak_name,
            pada=pada,
            total_pada_index=total_pada_idx,
            longitude_in_nakshatra=round(deg_in_nak, 4),
            longitude_in_pada=round(deg_in_pada, 4),
            elapsed_fraction=round(elapsed_frac, 6),
            ruler=meta[5],
            navamsha_sign_index=nav_sign_idx,
            navamsha_sign_name=nav_sign_name,
            gana=meta[0],
            nadi=meta[1],
            yoni=meta[2],
            tattva=meta[3],
            deity=meta[4],
        )
