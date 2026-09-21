"""Domain constants and enumerations for the astrology platform."""

from __future__ import annotations

from enum import IntEnum, StrEnum

# ─── Astrology System ────────────────────────────────────────────────────────


class AstrologySystem(StrEnum):
    """Supported astrology systems."""

    WESTERN = "western"
    VEDIC = "vedic"
    KP = "kp"
    BOTH = "both"


# ─── House Systems ───────────────────────────────────────────────────────────


class HouseSystem(StrEnum):
    """Supported house calculation systems."""

    PLACIDUS = "placidus"
    WHOLE_SIGN = "whole_sign"
    EQUAL = "equal"
    KOCH = "koch"

    def to_swisseph_char(self) -> str:
        """Convert to Swiss Ephemeris house system character."""
        mapping = {
            HouseSystem.PLACIDUS: "P",
            HouseSystem.WHOLE_SIGN: "W",
            HouseSystem.EQUAL: "E",
            HouseSystem.KOCH: "K",
        }
        return mapping[self]


# ─── Ayanamsa (Vedic) ───────────────────────────────────────────────────────


class Ayanamsa(StrEnum):
    """Supported ayanamsa systems for sidereal calculations."""

    LAHIRI = "lahiri"
    RAMAN = "raman"
    KRISHNAMURTI = "krishnamurti"
    FAGAN_BRADLEY = "fagan_bradley"
    TRUE_CITRA = "true_citra"


# ─── Planets ─────────────────────────────────────────────────────────────────


class Planet(IntEnum):
    """Planet identifiers matching Swiss Ephemeris constants."""

    SUN = 0
    MOON = 1
    MERCURY = 2
    VENUS = 3
    MARS = 4
    JUPITER = 5
    SATURN = 6
    URANUS = 7
    NEPTUNE = 8
    PLUTO = 9
    MEAN_NODE = 10  # Rahu (mean)
    TRUE_NODE = 11  # Rahu (true)
    # Ketu is derived as Rahu + 180°


# Vedic names for planets (Grahas)
GRAHA_NAMES: dict[Planet, str] = {
    Planet.SUN: "Surya",
    Planet.MOON: "Chandra",
    Planet.MERCURY: "Budha",
    Planet.VENUS: "Shukra",
    Planet.MARS: "Mangal",
    Planet.JUPITER: "Guru",
    Planet.SATURN: "Shani",
    Planet.MEAN_NODE: "Rahu",
}

PLANET_NAMES: dict[Planet, str] = {
    Planet.SUN: "Sun",
    Planet.MOON: "Moon",
    Planet.MERCURY: "Mercury",
    Planet.VENUS: "Venus",
    Planet.MARS: "Mars",
    Planet.JUPITER: "Jupiter",
    Planet.SATURN: "Saturn",
    Planet.URANUS: "Uranus",
    Planet.NEPTUNE: "Neptune",
    Planet.PLUTO: "Pluto",
    Planet.MEAN_NODE: "North Node",
    Planet.TRUE_NODE: "True Node",
}


# ─── Zodiac Signs ───────────────────────────────────────────────────────────


class Sign(IntEnum):
    """Zodiac signs (0-indexed for calculation, display as 1-12)."""

    ARIES = 0
    TAURUS = 1
    GEMINI = 2
    CANCER = 3
    LEO = 4
    VIRGO = 5
    LIBRA = 6
    SCORPIO = 7
    SAGITTARIUS = 8
    CAPRICORN = 9
    AQUARIUS = 10
    PISCES = 11


SIGN_NAMES: dict[Sign, str] = {
    Sign.ARIES: "Aries",
    Sign.TAURUS: "Taurus",
    Sign.GEMINI: "Gemini",
    Sign.CANCER: "Cancer",
    Sign.LEO: "Leo",
    Sign.VIRGO: "Virgo",
    Sign.LIBRA: "Libra",
    Sign.SCORPIO: "Scorpio",
    Sign.SAGITTARIUS: "Sagittarius",
    Sign.CAPRICORN: "Capricorn",
    Sign.AQUARIUS: "Aquarius",
    Sign.PISCES: "Pisces",
}

# Vedic sign names (Rashis)
RASHI_NAMES: dict[Sign, str] = {
    Sign.ARIES: "Mesha",
    Sign.TAURUS: "Vrishabha",
    Sign.GEMINI: "Mithuna",
    Sign.CANCER: "Karka",
    Sign.LEO: "Simha",
    Sign.VIRGO: "Kanya",
    Sign.LIBRA: "Tula",
    Sign.SCORPIO: "Vrishchika",
    Sign.SAGITTARIUS: "Dhanu",
    Sign.CAPRICORN: "Makara",
    Sign.AQUARIUS: "Kumbha",
    Sign.PISCES: "Meena",
}


# ─── Nakshatras ──────────────────────────────────────────────────────────────


class Nakshatra(IntEnum):
    """27 Nakshatras of Vedic astrology."""

    ASHWINI = 0
    BHARANI = 1
    KRITTIKA = 2
    ROHINI = 3
    MRIGASHIRSHA = 4
    ARDRA = 5
    PUNARVASU = 6
    PUSHYA = 7
    ASHLESHA = 8
    MAGHA = 9
    PURVA_PHALGUNI = 10
    UTTARA_PHALGUNI = 11
    HASTA = 12
    CHITRA = 13
    SWATI = 14
    VISHAKHA = 15
    ANURADHA = 16
    JYESHTHA = 17
    MULA = 18
    PURVA_ASHADHA = 19
    UTTARA_ASHADHA = 20
    SHRAVANA = 21
    DHANISHTHA = 22
    SHATABHISHA = 23
    PURVA_BHADRAPADA = 24
    UTTARA_BHADRAPADA = 25
    REVATI = 26


NAKSHATRA_NAMES: dict[Nakshatra, str] = {
    Nakshatra.ASHWINI: "Ashwini",
    Nakshatra.BHARANI: "Bharani",
    Nakshatra.KRITTIKA: "Krittika",
    Nakshatra.ROHINI: "Rohini",
    Nakshatra.MRIGASHIRSHA: "Mrigashirsha",
    Nakshatra.ARDRA: "Ardra",
    Nakshatra.PUNARVASU: "Punarvasu",
    Nakshatra.PUSHYA: "Pushya",
    Nakshatra.ASHLESHA: "Ashlesha",
    Nakshatra.MAGHA: "Magha",
    Nakshatra.PURVA_PHALGUNI: "Purva Phalguni",
    Nakshatra.UTTARA_PHALGUNI: "Uttara Phalguni",
    Nakshatra.HASTA: "Hasta",
    Nakshatra.CHITRA: "Chitra",
    Nakshatra.SWATI: "Swati",
    Nakshatra.VISHAKHA: "Vishakha",
    Nakshatra.ANURADHA: "Anuradha",
    Nakshatra.JYESHTHA: "Jyeshtha",
    Nakshatra.MULA: "Mula",
    Nakshatra.PURVA_ASHADHA: "Purva Ashadha",
    Nakshatra.UTTARA_ASHADHA: "Uttara Ashadha",
    Nakshatra.SHRAVANA: "Shravana",
    Nakshatra.DHANISHTHA: "Dhanishtha",
    Nakshatra.SHATABHISHA: "Shatabhisha",
    Nakshatra.PURVA_BHADRAPADA: "Purva Bhadrapada",
    Nakshatra.UTTARA_BHADRAPADA: "Uttara Bhadrapada",
    Nakshatra.REVATI: "Revati",
}

# Each nakshatra spans 13°20' = 800 arc-minutes
NAKSHATRA_SPAN_DEGREES: float = 13.0 + 20.0 / 60.0  # 13.3333...°

# Nakshatra ruling planets for Vimshottari Dasha (in order)
NAKSHATRA_RULERS: list[Planet] = [
    Planet.MEAN_NODE,  # Ketu (derived from Rahu node)
    Planet.VENUS,
    Planet.SUN,
    Planet.MOON,
    Planet.MARS,
    Planet.MEAN_NODE,  # Rahu
    Planet.JUPITER,
    Planet.SATURN,
    Planet.MERCURY,
]

# Vimshottari Dasha periods in years (total cycle = 120 years)
# Order: Ketu, Venus, Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury
VIMSHOTTARI_PERIODS: dict[str, float] = {
    "Ketu": 7.0,
    "Venus": 20.0,
    "Sun": 6.0,
    "Moon": 10.0,
    "Mars": 7.0,
    "Rahu": 18.0,
    "Jupiter": 16.0,
    "Saturn": 19.0,
    "Mercury": 17.0,
}

VIMSHOTTARI_ORDER: list[str] = [
    "Ketu",
    "Venus",
    "Sun",
    "Moon",
    "Mars",
    "Rahu",
    "Jupiter",
    "Saturn",
    "Mercury",
]

VIMSHOTTARI_TOTAL_YEARS: float = 120.0

# KP (Krishnamurti Paddhati) sub-lord period spans within each Nakshatra
# Each Nakshatra (13°20' = 13.3333°) is divided into 9 sub-lords proportional to Vimshottari periods
# Sub-lord span = (planet_period / 120) * 13.3333°
KP_SUB_PERIODS: dict[str, float] = {
    lord: (years / VIMSHOTTARI_TOTAL_YEARS) * NAKSHATRA_SPAN_DEGREES
    for lord, years in VIMSHOTTARI_PERIODS.items()
}


# ─── Aspects ─────────────────────────────────────────────────────────────────


class AspectType(StrEnum):
    """Major Western aspects."""

    CONJUNCTION = "conjunction"
    OPPOSITION = "opposition"
    TRINE = "trine"
    SQUARE = "square"
    SEXTILE = "sextile"
    QUINCUNX = "quincunx"
    SEMI_SEXTILE = "semi_sextile"


# Aspect angles in degrees
ASPECT_ANGLES: dict[AspectType, float] = {
    AspectType.CONJUNCTION: 0.0,
    AspectType.OPPOSITION: 180.0,
    AspectType.TRINE: 120.0,
    AspectType.SQUARE: 90.0,
    AspectType.SEXTILE: 60.0,
    AspectType.QUINCUNX: 150.0,
    AspectType.SEMI_SEXTILE: 30.0,
}

# Default orbs for major aspects (degrees)
DEFAULT_ORBS: dict[AspectType, float] = {
    AspectType.CONJUNCTION: 8.0,
    AspectType.OPPOSITION: 8.0,
    AspectType.TRINE: 8.0,
    AspectType.SQUARE: 7.0,
    AspectType.SEXTILE: 6.0,
    AspectType.QUINCUNX: 3.0,
    AspectType.SEMI_SEXTILE: 3.0,
}


# ─── Subscription ───────────────────────────────────────────────────────────


class SubscriptionPlan(StrEnum):
    FREE = "free"
    PRO = "pro"
    PREMIUM = "premium"


# ─── Readings ────────────────────────────────────────────────────────────────


class ReadingType(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


# ─── Life Areas ──────────────────────────────────────────────────────────────


class LifeArea(StrEnum):
    CAREER = "career"
    RELATIONSHIPS = "relationships"
    MONEY = "money"
    HEALTH = "health"
    PERSONAL_GROWTH = "personal_growth"
    SPIRITUALITY = "spirituality"
    GENERAL = "general"


# ─── Event Types ─────────────────────────────────────────────────────────────


class AstroEventType(StrEnum):
    PLANETARY_INGRESS = "planetary_ingress"
    RETROGRADE_START = "retrograde_start"
    RETROGRADE_END = "retrograde_end"
    STATIONARY = "stationary"
    MAJOR_ASPECT = "major_aspect"
    LUNAR_PHASE = "lunar_phase"
    ECLIPSE = "eclipse"
    TRANSIT_TO_NATAL = "transit_to_natal"
    DASHA_CHANGE = "dasha_change"
    NAKSHATRA_CHANGE = "nakshatra_change"


# ─── Birth Time Accuracy ────────────────────────────────────────────────────


class BirthTimeAccuracy(StrEnum):
    EXACT = "exact"  # From birth certificate with time
    APPROXIMATE = "approximate"  # Rounded or from memory
    RECTIFIED = "rectified"  # Astrologically rectified
    UNKNOWN = "unknown"  # Time unknown (noon default)
