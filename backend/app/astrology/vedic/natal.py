"""Vedic Natal Chart (Kundli) calculation and synthesis engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime

from app.astrology.ephemeris import EphemerisService
from app.astrology.vedic.antardasha import ActiveDashaInfo, DashaTreeBuilder
from app.astrology.vedic.dashas import MahadashaPeriod, VimshottariDashaEngine
from app.astrology.vedic.divisional_charts import DivisionalChartEngine, DivisionalChartResult
from app.astrology.vedic.houses import CharaKaraka, VedicHouseCalculator, VedicHouseInfo
from app.astrology.vedic.nakshatras import NakshatraCalculator, NakshatraInfo
from app.astrology.vedic.rashis import PlanetaryDignity, RashiCalculator
from app.astrology.vedic.yogas import VedicYogaEngine, VedicYogaResult
from app.config.constants import (
    RASHI_NAMES,
    AstrologySystem,
    Ayanamsa,
    HouseSystem,
    Planet,
    Sign,
)


@dataclass(frozen=True)
class VedicGrahaInfo:
    """Rich Vedic representation of a celestial body (Graha)."""

    name: str  # e.g. "Surya", "Chandra"
    western_name: str  # e.g. "Sun", "Moon"
    longitude: float  # Absolute sidereal longitude [0, 360)
    latitude: float
    speed_longitude: float
    is_retrograde: bool
    rashi_index: int  # 0 = Mesha .. 11 = Meena
    rashi_name: str
    degree_in_rashi: float  # [0, 30)
    house_number: int  # 1 through 12
    nakshatra: NakshatraInfo
    dignity: PlanetaryDignity
    is_vargottama: bool  # Same sign in D1 (Rashi) and D9 (Navamsha)


@dataclass(frozen=True)
class VedicNatalChartResult:
    """Complete structured Vedic Natal Chart (Kundli) payload."""

    system: str
    ayanamsa: str
    ayanamsa_value: float
    datetime_utc: datetime
    julian_day: float
    latitude: float
    longitude: float
    ascendant_longitude: float
    ascendant_rashi: str
    ascendant_nakshatra: NakshatraInfo
    grahas: list[VedicGrahaInfo]
    bhavas: list[VedicHouseInfo]
    karakas: list[CharaKaraka]
    yogas: list[VedicYogaResult]
    d1_rashi_chart: DivisionalChartResult
    d9_navamsha_chart: DivisionalChartResult
    mahadashas: list[MahadashaPeriod]
    active_dasha_at_birth: ActiveDashaInfo

    def to_dict(self) -> dict:
        """Serialize full Vedic chart to dictionary."""
        return {
            "system": self.system,
            "ayanamsa": self.ayanamsa,
            "ayanamsa_value": round(self.ayanamsa_value, 4),
            "datetime_utc": self.datetime_utc.isoformat(),
            "julian_day": self.julian_day,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "ascendant_longitude": round(self.ascendant_longitude, 4),
            "ascendant_rashi": self.ascendant_rashi,
            "ascendant_nakshatra": asdict(self.ascendant_nakshatra),
            "grahas": [
                {
                    **asdict(g),
                    "dignity": g.dignity.value,
                    "nakshatra": asdict(g.nakshatra),
                }
                for g in self.grahas
            ],
            "planets": {
                g.western_name: {
                    **asdict(g),
                    "dignity": g.dignity.value,
                    "nakshatra": asdict(g.nakshatra),
                }
                for g in self.grahas
            },
            "bhavas": [asdict(b) for b in self.bhavas],
            "houses": {b.house_number: asdict(b) for b in self.bhavas},
            "karakas": [asdict(k) for k in self.karakas],
            "yogas": [
                {
                    **asdict(y),
                    "category": y.category.value,
                }
                for y in self.yogas
            ],
            "d1_rashi_chart": self.d1_rashi_chart.to_dict(),
            "d9_navamsha_chart": self.d9_navamsha_chart.to_dict(),
            "mahadashas": [
                {
                    "lord": m.lord,
                    "start_date": m.start_date.isoformat(),
                    "end_date": m.end_date.isoformat(),
                    "duration_years": m.duration_years,
                }
                for m in self.mahadashas
            ],
            "active_dasha_at_birth": self.active_dasha_at_birth.to_dict(),
        }


class VedicNatalChartEngine:
    """Coordinates calculation of Vedic natal charts, planetary dignities, vargas, dashas, and yogas."""

    def __init__(self, ephemeris: EphemerisService | None = None) -> None:
        self.ephemeris = ephemeris or EphemerisService()

    def calculate_chart(
        self,
        dt_utc: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: Ayanamsa = Ayanamsa.LAHIRI,
    ) -> VedicNatalChartResult:
        """
        Compute complete Vedic Sidereal natal chart.
        """
        dt_utc = dt_utc.replace(tzinfo=UTC) if dt_utc.tzinfo is None else dt_utc.astimezone(UTC)
        jd = self.ephemeris.datetime_to_julian_day(dt_utc)
        ayanamsa_val = self.ephemeris.get_ayanamsa_value(jd, ayanamsa)

        # 1. Vedic Planets (Surya through Shani + Rahu + Ketu)
        planets_to_calc = [
            Planet.SUN,
            Planet.MOON,
            Planet.MERCURY,
            Planet.VENUS,
            Planet.MARS,
            Planet.JUPITER,
            Planet.SATURN,
            Planet.MEAN_NODE,
        ]

        raw_planets = [
            self.ephemeris.calculate_planet(
                jd=jd,
                planet=p,
                system=AstrologySystem.VEDIC,
                ayanamsa=ayanamsa,
            )
            for p in planets_to_calc
        ]

        # Calculate Ketu as Rahu + 180°
        rahu_p = next(p for p in raw_planets if p.name in ("North Node", "True Node"))
        ketu_lon = (rahu_p.longitude + 180.0) % 360.0
        ketu_sign_idx = int(ketu_lon // 30) % 12
        ketu_sign_name = RASHI_NAMES[Sign(ketu_sign_idx)]

        # Calculate Sidereal Ascendant (Lagna)
        # Compute tropical houses first then subtract ayanamsa
        trop_houses = self.ephemeris.calculate_houses(
            jd=jd,
            latitude=latitude,
            longitude=longitude,
            system=HouseSystem.WHOLE_SIGN,
        )
        sidereal_asc = (trop_houses.ascendant - ayanamsa_val) % 360.0
        lagna_rashi_idx = int(sidereal_asc // 30) % 12
        asc_nak = NakshatraCalculator.calculate_from_longitude(sidereal_asc)

        # 2. Bhavas
        bhavas = VedicHouseCalculator.analyze_bhavas(
            lagna_longitude=sidereal_asc,
            planets=raw_planets,
        )

        # 3. Rich Graha structures
        grahas: list[VedicGrahaInfo] = []
        dignity_map: dict[str, PlanetaryDignity] = {}

        for p in raw_planets:
            p_name = "Rahu" if p.name in ("North Node", "True Node") else p.name
            rashi_idx = int(p.longitude // 30) % 12
            deg_in_rashi = p.longitude % 30.0
            h_num = VedicHouseCalculator.get_house_for_rashi(rashi_idx, lagna_rashi_idx)
            nak = NakshatraCalculator.calculate_from_longitude(p.longitude)
            dignity = RashiCalculator.evaluate_dignity(
                planet_name=p_name,
                sign_index=rashi_idx,
                degree_in_sign=deg_in_rashi,
            )
            dignity_map[p_name] = dignity
            is_vargottama = rashi_idx == nak.navamsha_sign_index

            grahas.append(
                VedicGrahaInfo(
                    name=p_name,
                    western_name=p.name,
                    longitude=round(p.longitude, 4),
                    latitude=round(p.latitude, 4),
                    speed_longitude=round(p.speed_longitude, 4),
                    is_retrograde=p.is_retrograde,
                    rashi_index=rashi_idx,
                    rashi_name=RASHI_NAMES[Sign(rashi_idx)],
                    degree_in_rashi=round(deg_in_rashi, 4),
                    house_number=h_num,
                    nakshatra=nak,
                    dignity=dignity,
                    is_vargottama=is_vargottama,
                )
            )

        # Add Ketu
        ketu_nak = NakshatraCalculator.calculate_from_longitude(ketu_lon)
        ketu_h_num = VedicHouseCalculator.get_house_for_rashi(ketu_sign_idx, lagna_rashi_idx)
        ketu_dignity = RashiCalculator.evaluate_dignity("Ketu", ketu_sign_idx, ketu_lon % 30.0)
        dignity_map["Ketu"] = ketu_dignity
        grahas.append(
            VedicGrahaInfo(
                name="Ketu",
                western_name="South Node",
                longitude=round(ketu_lon, 4),
                latitude=round(-rahu_p.latitude, 4),
                speed_longitude=round(rahu_p.speed_longitude, 4),
                is_retrograde=rahu_p.is_retrograde,
                rashi_index=ketu_sign_idx,
                rashi_name=ketu_sign_name,
                degree_in_rashi=round(ketu_lon % 30.0, 4),
                house_number=ketu_h_num,
                nakshatra=ketu_nak,
                dignity=ketu_dignity,
                is_vargottama=(ketu_sign_idx == ketu_nak.navamsha_sign_index),
            )
        )

        # 4. Jaimini Karakas
        karakas = VedicHouseCalculator.calculate_jaimini_karakas(raw_planets)

        # 5. Yogas & Doshas
        yogas = VedicYogaEngine.detect_yogas(
            lagna_longitude=sidereal_asc,
            planets=raw_planets,
            bhavas=bhavas,
            dignities=dignity_map,
        )

        # 6. Divisional Charts (D1 & D9)
        d1_chart = DivisionalChartEngine.generate_divisional_chart(
            division=1,
            ascendant_lon=sidereal_asc,
            planets=raw_planets,
        )
        d9_chart = DivisionalChartEngine.generate_divisional_chart(
            division=9,
            ascendant_lon=sidereal_asc,
            planets=raw_planets,
        )

        # 7. Vimshottari Dashas
        moon_graha = next(g for g in grahas if g.name == "Moon")
        mahadashas = VimshottariDashaEngine.calculate_mahadashas(
            moon_sidereal_longitude=moon_graha.longitude,
            birth_datetime_utc=dt_utc,
            cycle_count=1,
        )
        active_dasha = DashaTreeBuilder.find_active_dasha(
            moon_sidereal_lon=moon_graha.longitude,
            birth_utc=dt_utc,
            target_utc=dt_utc,
        )

        return VedicNatalChartResult(
            system=AstrologySystem.VEDIC.value,
            ayanamsa=ayanamsa.value,
            ayanamsa_value=ayanamsa_val,
            datetime_utc=dt_utc,
            julian_day=round(jd, 6),
            latitude=latitude,
            longitude=longitude,
            ascendant_longitude=sidereal_asc,
            ascendant_rashi=RASHI_NAMES[Sign(lagna_rashi_idx)],
            ascendant_nakshatra=asc_nak,
            grahas=grahas,
            bhavas=bhavas,
            karakas=karakas,
            yogas=yogas,
            d1_rashi_chart=d1_chart,
            d9_navamsha_chart=d9_chart,
            mahadashas=mahadashas,
            active_dasha_at_birth=active_dasha,
        )
