"""Western Natal Chart calculation and synthesis engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime

from app.astrology.ephemeris import EphemerisService, PlanetPosition
from app.astrology.western.aspects import AspectCalculator, AspectInfo, AspectPattern
from app.astrology.western.houses import WesternHouseCalculator, WesternHouseInfo
from app.config.constants import AstrologySystem, HouseSystem, Planet, Sign

# Elements and Modalities mappings for 12 signs
ELEMENT_MAP: dict[int, str] = {
    0: "Fire",
    1: "Earth",
    2: "Air",
    3: "Water",  # Aries, Taurus, Gemini, Cancer
    4: "Fire",
    5: "Earth",
    6: "Air",
    7: "Water",  # Leo, Virgo, Libra, Scorpio
    8: "Fire",
    9: "Earth",
    10: "Air",
    11: "Water",  # Sag, Cap, Aqua, Pisces
}

MODALITY_MAP: dict[int, str] = {
    0: "Cardinal",
    1: "Fixed",
    2: "Mutable",  # Aries, Taurus, Gemini
    3: "Cardinal",
    4: "Fixed",
    5: "Mutable",  # Cancer, Leo, Virgo
    6: "Cardinal",
    7: "Fixed",
    8: "Mutable",  # Libra, Scorpio, Sag
    9: "Cardinal",
    10: "Fixed",
    11: "Mutable",  # Cap, Aqua, Pisces
}

POLARITY_MAP: dict[int, str] = {
    0: "Yang (Masculine)",
    1: "Yin (Feminine)",
    2: "Yang (Masculine)",
    3: "Yin (Feminine)",
    4: "Yang (Masculine)",
    5: "Yin (Feminine)",
    6: "Yang (Masculine)",
    7: "Yin (Feminine)",
    8: "Yang (Masculine)",
    9: "Yin (Feminine)",
    10: "Yang (Masculine)",
    11: "Yin (Feminine)",
}


@dataclass(frozen=True)
class ElementalBalance:
    """Distribution of planets across elements and modalities."""

    fire: int
    earth: int
    air: int
    water: int
    cardinal: int
    fixed: int
    mutable: int
    yang: int
    yin: int
    dominant_element: str
    dominant_modality: str


@dataclass(frozen=True)
class WesternNatalChartResult:
    """Complete structured Western Natal Chart payload."""

    system: str
    house_system: str
    datetime_utc: datetime
    julian_day: float
    latitude: float
    longitude: float
    planets: list[PlanetPosition]
    houses: list[WesternHouseInfo]
    angles: dict[str, float]
    aspects: list[AspectInfo]
    patterns: list[AspectPattern]
    balance: ElementalBalance
    sun_sign: str
    moon_sign: str
    ascendant_sign: str
    chart_signature: str

    def to_dict(self) -> dict:
        """Convert entire chart result to JSON-serializable dictionary."""
        return {
            "system": self.system,
            "house_system": self.house_system,
            "datetime_utc": self.datetime_utc.isoformat(),
            "julian_day": self.julian_day,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "planets": {p.name: asdict(p) for p in self.planets},
            "planets_list": [asdict(p) for p in self.planets],
            "houses": [asdict(h) for h in self.houses],
            "angles": self.angles,
            "aspects": [
                {
                    **asdict(a),
                    "aspect_type": a.aspect_type.value,
                }
                for a in self.aspects
            ],
            "patterns": [asdict(pt) for pt in self.patterns],
            "balance": asdict(self.balance),
            "sun_sign": self.sun_sign,
            "moon_sign": self.moon_sign,
            "ascendant_sign": self.ascendant_sign,
            "chart_signature": self.chart_signature,
        }


class WesternNatalChartEngine:
    """Coordinates the end-to-end Western natal chart calculation pipeline."""

    def __init__(self, ephemeris: EphemerisService | None = None) -> None:
        self.ephemeris = ephemeris or EphemerisService()

    def calculate_chart(
        self,
        dt_utc: datetime,
        latitude: float,
        longitude: float,
        house_system: HouseSystem = HouseSystem.PLACIDUS,
    ) -> WesternNatalChartResult:
        """
        Execute full astronomical calculations, aspect analysis, and element synthesis.
        """
        dt_utc = dt_utc.replace(tzinfo=UTC) if dt_utc.tzinfo is None else dt_utc.astimezone(UTC)
        jd = self.ephemeris.datetime_to_julian_day(dt_utc)

        # 1. Ephemeris planetary positions
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

        planets = [
            self.ephemeris.calculate_planet(
                jd=jd,
                planet=p,
                system=AstrologySystem.WESTERN,
            )
            for p in planets_to_calc
        ]

        # 2. House calculation
        house_pos = self.ephemeris.calculate_houses(
            jd=jd,
            latitude=latitude,
            longitude=longitude,
            system=house_system,
        )

        planet_lons = {p.name: p.longitude for p in planets}
        houses = WesternHouseCalculator.analyze_houses(
            house_cusps=house_pos.cusps,
            planet_positions=planet_lons,
            system=house_system,
        )

        # 3. Angles
        asc_sign_idx = int(house_pos.ascendant // 30)
        from app.config.constants import SIGN_NAMES

        asc_sign_name = SIGN_NAMES[Sign(asc_sign_idx)]

        angles = {
            "ascendant": round(house_pos.ascendant, 4),
            "midheaven": round(house_pos.midheaven, 4),
            "armc": round(house_pos.armc, 4),
            "vertex": round(house_pos.vertex, 4),
            "descendant": round((house_pos.ascendant + 180.0) % 360.0, 4),
            "imum_coeli": round((house_pos.midheaven + 180.0) % 360.0, 4),
        }

        # 4. Aspects and patterns
        aspects = AspectCalculator.calculate_aspects(planets)
        patterns = AspectCalculator.detect_patterns(planets, aspects)

        # 5. Elemental and Modality Balance (evaluated across 10 traditional/modern bodies)
        counts = {
            "Fire": 0,
            "Earth": 0,
            "Air": 0,
            "Water": 0,
            "Cardinal": 0,
            "Fixed": 0,
            "Mutable": 0,
            "Yang": 0,
            "Yin": 0,
        }

        for p in planets:
            if p.name in ("North Node", "True Node"):
                continue
            counts[ELEMENT_MAP[p.sign_index]] += 1
            counts[MODALITY_MAP[p.sign_index]] += 1
            pol = "Yang" if "Yang" in POLARITY_MAP[p.sign_index] else "Yin"
            counts[pol] += 1

        dom_element = max(["Fire", "Earth", "Air", "Water"], key=lambda k: counts[k])
        dom_modality = max(["Cardinal", "Fixed", "Mutable"], key=lambda k: counts[k])

        balance = ElementalBalance(
            fire=counts["Fire"],
            earth=counts["Earth"],
            air=counts["Air"],
            water=counts["Water"],
            cardinal=counts["Cardinal"],
            fixed=counts["Fixed"],
            mutable=counts["Mutable"],
            yang=counts["Yang"],
            yin=counts["Yin"],
            dominant_element=dom_element,
            dominant_modality=dom_modality,
        )

        # Sun and Moon Signs
        sun_p = next(p for p in planets if p.name == "Sun")
        moon_p = next(p for p in planets if p.name == "Moon")

        chart_signature = f"{dom_modality} {dom_element}"

        return WesternNatalChartResult(
            system=AstrologySystem.WESTERN.value,
            house_system=house_system.value,
            datetime_utc=dt_utc,
            julian_day=round(jd, 6),
            latitude=latitude,
            longitude=longitude,
            planets=planets,
            houses=houses,
            angles=angles,
            aspects=aspects,
            patterns=patterns,
            balance=balance,
            sun_sign=sun_p.sign_name,
            moon_sign=moon_p.sign_name,
            ascendant_sign=asc_sign_name,
            chart_signature=chart_signature,
        )
