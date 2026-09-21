"""KP (Krishnamurti Paddhati) Natal Chart calculation and synthesis engine.

Uses Placidus house system (mandatory for KP), Krishnamurti Ayanamsa, and
computes full sub-lord chains, significator analysis, cuspal sub-lords,
Vimshottari Dasha with KP event markers, and Ruling Planets for event timing.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.astrology.ephemeris import EphemerisService, PlanetPosition
from app.astrology.kp.cuspal_analysis import KpCuspalAnalysis, KpCuspInfo
from app.astrology.kp.significators import KpPlanetSignification, KpSignificatorEngine
from app.astrology.kp.sublords import KpSubLordCalculator, KpSubLordInfo
from app.astrology.vedic.antardasha import ActiveDashaInfo, DashaTreeBuilder
from app.astrology.vedic.dashas import MahadashaPeriod, VimshottariDashaEngine
from app.astrology.vedic.houses import VedicHouseCalculator, VedicHouseInfo
from app.astrology.vedic.nakshatras import NakshatraCalculator, NakshatraInfo
from app.astrology.vedic.rashis import PlanetaryDignity, RashiCalculator
from app.config.constants import (
    RASHI_NAMES,
    VIMSHOTTARI_ORDER,
    AstrologySystem,
    Ayanamsa,
    HouseSystem,
    Planet,
    Sign,
)


@dataclass(frozen=True)
class KpGrahaInfo:
    """KP-enriched representation of a celestial body."""

    name: str  # e.g. "Surya", "Rahu"
    western_name: str  # e.g. "Sun", "North Node"
    longitude: float  # Sidereal longitude [0, 360)
    latitude: float
    speed_longitude: float
    is_retrograde: bool
    rashi_index: int
    rashi_name: str
    degree_in_rashi: float
    house_number: int  # Placidus house (1-12)
    nakshatra: NakshatraInfo
    dignity: PlanetaryDignity
    # KP-specific fields
    star_lord: str
    sub_lord: str
    sub_sub_lord: str
    kp_number: int


@dataclass(frozen=True)
class KpRulingPlanets:
    """Ruling Planets at a given moment — used for precise event timing in KP."""

    moment_utc: str
    ascendant_sign_lord: str  # Lord of the rising sign
    ascendant_star_lord: str  # Nakshatra lord of the ascendant degree
    ascendant_sub_lord: str  # Sub-lord of the ascendant
    moon_sign_lord: str  # Lord of Moon's sign
    moon_star_lord: str  # Nakshatra lord of Moon's degree
    moon_sub_lord: str  # Sub-lord of Moon
    day_lord: str  # Planet ruling the day of the week

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class KpNatalChartResult:
    """Complete KP Natal Chart payload."""

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
    ascendant_sublord_info: KpSubLordInfo
    grahas: list[KpGrahaInfo]
    bhavas: list[VedicHouseInfo]
    cuspal_analysis: list[KpCuspInfo]
    significators: dict[str, KpPlanetSignification]
    mahadashas: list[MahadashaPeriod]
    active_dasha_at_birth: ActiveDashaInfo
    ruling_planets_at_birth: KpRulingPlanets
    ruling_planets_at_query: KpRulingPlanets | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize full KP chart to dictionary."""
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
            "ascendant_sublord": {
                "star_lord": self.ascendant_sublord_info.star_lord,
                "sub_lord": self.ascendant_sublord_info.sub_lord,
                "sub_sub_lord": self.ascendant_sublord_info.sub_sub_lord,
            },
            "grahas": [
                {
                    **{
                        k: v for k, v in asdict(g).items()
                        if k not in ("dignity", "nakshatra")
                    },
                    "dignity": g.dignity.value,
                    "nakshatra": asdict(g.nakshatra),
                }
                for g in self.grahas
            ],
            "planets": {
                g.western_name: {
                    **{
                        k: v for k, v in asdict(g).items()
                        if k not in ("dignity", "nakshatra")
                    },
                    "dignity": g.dignity.value,
                    "nakshatra": asdict(g.nakshatra),
                }
                for g in self.grahas
            },
            "bhavas": [asdict(b) for b in self.bhavas],
            "houses": {b.house_number: asdict(b) for b in self.bhavas},
            "cuspal_analysis": [
                asdict(c) for c in self.cuspal_analysis
            ],
            "significators": {
                name: asdict(sig) for name, sig in self.significators.items()
            },
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
            "ruling_planets_at_birth": self.ruling_planets_at_birth.to_dict(),
            "ruling_planets_at_query": (
                self.ruling_planets_at_query.to_dict()
                if self.ruling_planets_at_query
                else None
            ),
        }


# Day of week to ruling planet (KP system uses standard Vedic day lords)
DAY_LORDS: dict[int, str] = {
    0: "Moon",     # Monday
    1: "Mars",     # Tuesday
    2: "Mercury",  # Wednesday
    3: "Jupiter",  # Thursday
    4: "Venus",    # Friday
    5: "Saturn",   # Saturday
    6: "Sun",      # Sunday
}


class KpNatalChartEngine:
    """Coordinates full KP natal chart calculation.

    Uses Placidus house system (mandatory for KP) with Krishnamurti Ayanamsa
    to compute planets, cusps, sub-lords, significators, dasha, and ruling planets.
    """

    def __init__(self, ephemeris: EphemerisService | None = None) -> None:
        self.ephemeris = ephemeris or EphemerisService()

    def calculate_chart(
        self,
        dt_utc: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: Ayanamsa = Ayanamsa.KRISHNAMURTI,
        target_utc: datetime | None = None,
        query_dt_utc: datetime | None = None,
    ) -> KpNatalChartResult:
        """Compute complete KP Natal Chart.

        Args:
            dt_utc: Birth datetime in UTC.
            latitude: Birth latitude.
            longitude: Birth longitude.
            ayanamsa: Sidereal ayanamsa (defaults to Krishnamurti).
            target_utc: Optional target datetime for ruling planets query.
            query_dt_utc: Optional alias for target_utc.
        """
        dt_utc = dt_utc.replace(tzinfo=UTC) if dt_utc.tzinfo is None else dt_utc.astimezone(UTC)
        jd = self.ephemeris.datetime_to_julian_day(dt_utc)
        ayanamsa_val = self.ephemeris.get_ayanamsa_value(jd, ayanamsa)

        # ── 1. Sidereal Planets (KP uses Krishnamurti Ayanamsa) ──
        planets_to_calc = [
            Planet.SUN, Planet.MOON, Planet.MERCURY, Planet.VENUS,
            Planet.MARS, Planet.JUPITER, Planet.SATURN, Planet.MEAN_NODE,
        ]

        raw_planets: list[PlanetPosition] = [
            self.ephemeris.calculate_planet(
                jd=jd, planet=p,
                system=AstrologySystem.VEDIC,  # Sidereal calculation
                ayanamsa=ayanamsa,
            )
            for p in planets_to_calc
        ]

        # Ketu = Rahu + 180°
        rahu_p = next(p for p in raw_planets if p.name in ("North Node", "True Node"))
        ketu_lon = (rahu_p.longitude + 180.0) % 360.0

        # ── 2. Placidus House Cusps (mandatory for KP) ──
        trop_houses = self.ephemeris.calculate_houses(
            jd=jd, latitude=latitude, longitude=longitude,
            house_system=HouseSystem.PLACIDUS,
        )

        # Sidereal Ascendant
        sidereal_asc = (trop_houses.ascendant - ayanamsa_val) % 360.0
        lagna_rashi_idx = int(sidereal_asc // 30) % 12
        asc_nak = NakshatraCalculator.calculate_from_longitude(sidereal_asc)
        asc_sublord = KpSubLordCalculator.calculate_sublord(sidereal_asc)

        # ── 3. Bhavas (using Placidus cusps → planet house assignment) ──
        # In KP, planets are assigned to houses based on Placidus cusp boundaries
        sidereal_cusps = [(c - ayanamsa_val) % 360.0 for c in trop_houses.cusps]
        planet_houses = self._assign_placidus_houses(raw_planets, sidereal_cusps, ketu_lon)

        # Also compute Whole Sign bhavas for occupant/lord analysis
        bhavas = VedicHouseCalculator.analyze_bhavas(
            lagna_longitude=sidereal_asc,
            planets=raw_planets,
        )

        # ── 4. Build KP Graha Info ──
        grahas: list[KpGrahaInfo] = []
        for p in raw_planets:
            p_name = "Rahu" if p.name in ("North Node", "True Node") else p.name
            rashi_idx = int(p.longitude // 30) % 12
            deg_in_rashi = p.longitude % 30.0
            nak = NakshatraCalculator.calculate_from_longitude(p.longitude)
            kp_info = KpSubLordCalculator.calculate_sublord(p.longitude)
            dignity = RashiCalculator.evaluate_dignity(p_name, rashi_idx, deg_in_rashi)
            h_num = planet_houses.get(p_name, VedicHouseCalculator.get_house_for_rashi(rashi_idx, lagna_rashi_idx))

            grahas.append(KpGrahaInfo(
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
                star_lord=kp_info.star_lord,
                sub_lord=kp_info.sub_lord,
                sub_sub_lord=kp_info.sub_sub_lord,
                kp_number=KpSubLordCalculator.get_kp_number(p.longitude),
            ))

        # Add Ketu
        ketu_sign_idx = int(ketu_lon // 30) % 12
        ketu_nak = NakshatraCalculator.calculate_from_longitude(ketu_lon)
        ketu_kp = KpSubLordCalculator.calculate_sublord(ketu_lon)
        ketu_dignity = RashiCalculator.evaluate_dignity("Ketu", ketu_sign_idx, ketu_lon % 30.0)
        ketu_house = planet_houses.get("Ketu", VedicHouseCalculator.get_house_for_rashi(ketu_sign_idx, lagna_rashi_idx))

        grahas.append(KpGrahaInfo(
            name="Ketu",
            western_name="South Node",
            longitude=round(ketu_lon, 4),
            latitude=round(-rahu_p.latitude, 4),
            speed_longitude=round(rahu_p.speed_longitude, 4),
            is_retrograde=rahu_p.is_retrograde,
            rashi_index=ketu_sign_idx,
            rashi_name=RASHI_NAMES[Sign(ketu_sign_idx)],
            degree_in_rashi=round(ketu_lon % 30.0, 4),
            house_number=ketu_house,
            nakshatra=ketu_nak,
            dignity=ketu_dignity,
            star_lord=ketu_kp.star_lord,
            sub_lord=ketu_kp.sub_lord,
            sub_sub_lord=ketu_kp.sub_sub_lord,
            kp_number=KpSubLordCalculator.get_kp_number(ketu_lon),
        ))

        # ── 5. Cuspal Sub-lord Analysis ──
        # Build planet-house and house-lord maps for cuspal assessment
        p_house_map: dict[str, int] = {}
        for bhava in bhavas:
            for occ in bhava.occupants:
                p_house_map[occ] = bhava.house_number
        h_lord_map: dict[int, str] = {b.house_number: b.lord for b in bhavas}

        cuspal_analysis = KpCuspalAnalysis.analyze_cusps(
            placidus_cusps=trop_houses.cusps,
            ayanamsa_value=ayanamsa_val,
            planet_house_map=p_house_map,
            house_lord_map=h_lord_map,
        )

        # ── 6. Significator Analysis ──
        significators = KpSignificatorEngine.analyze_significators(
            planets=raw_planets,
            bhavas=bhavas,
            lagna_rashi_idx=lagna_rashi_idx,
        )

        # ── 7. Vimshottari Dasha (KP uses same sequence, different ayanamsa) ──
        moon_graha = next(g for g in grahas if g.name in ("Moon", "Chandra"))
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

        # ── 8. Ruling Planets at Birth ──
        rp_birth = self._calculate_ruling_planets(
            dt_utc=dt_utc,
            sidereal_asc=sidereal_asc,
            moon_lon=moon_graha.longitude,
        )

        # ── 9. Ruling Planets at Query (if target_utc or query_dt_utc provided) ──
        rp_query = None
        effective_query_dt = query_dt_utc or target_utc
        if effective_query_dt:
            target_dt_utc = effective_query_dt.replace(tzinfo=UTC) if effective_query_dt.tzinfo is None else effective_query_dt.astimezone(UTC)
            target_jd = self.ephemeris.datetime_to_julian_day(target_dt_utc)
            target_ayan = self.ephemeris.get_ayanamsa_value(target_jd, ayanamsa)

            # Transit Moon at target
            target_moon = self.ephemeris.calculate_planet(
                jd=target_jd, planet=Planet.MOON,
                system=AstrologySystem.VEDIC, ayanamsa=ayanamsa,
            )
            # Transit Ascendant at target
            target_houses = self.ephemeris.calculate_houses(
                jd=target_jd, latitude=latitude, longitude=longitude,
                house_system=HouseSystem.PLACIDUS,
            )
            target_sid_asc = (target_houses.ascendant - target_ayan) % 360.0

            rp_query = self._calculate_ruling_planets(
                dt_utc=target_dt_utc,
                sidereal_asc=target_sid_asc,
                moon_lon=target_moon.longitude,
            )

        return KpNatalChartResult(
            system=AstrologySystem.KP.value,
            ayanamsa=ayanamsa.value,
            ayanamsa_value=ayanamsa_val,
            datetime_utc=dt_utc,
            julian_day=round(jd, 6),
            latitude=latitude,
            longitude=longitude,
            ascendant_longitude=sidereal_asc,
            ascendant_rashi=RASHI_NAMES[Sign(lagna_rashi_idx)],
            ascendant_nakshatra=asc_nak,
            ascendant_sublord_info=asc_sublord,
            grahas=grahas,
            bhavas=bhavas,
            cuspal_analysis=cuspal_analysis,
            significators=significators,
            mahadashas=mahadashas,
            active_dasha_at_birth=active_dasha,
            ruling_planets_at_birth=rp_birth,
            ruling_planets_at_query=rp_query,
        )

    def _assign_placidus_houses(
        self,
        planets: list[PlanetPosition],
        sidereal_cusps: list[float],
        ketu_lon: float,
    ) -> dict[str, int]:
        """Assign planets to Placidus houses based on cusp boundaries.

        In KP, a planet belongs to the house whose cusp it falls after, until
        the next cusp. This differs from Vedic Whole Sign system.
        """
        result: dict[str, int] = {}

        all_planets: list[tuple[str, float]] = []
        for p in planets:
            p_name = "Rahu" if p.name in ("North Node", "True Node") else p.name
            all_planets.append((p_name, p.longitude))
        all_planets.append(("Ketu", ketu_lon))

        for p_name, p_lon in all_planets:
            house = self._find_house_for_longitude(p_lon, sidereal_cusps)
            result[p_name] = house

        return result

    @staticmethod
    def _find_house_for_longitude(lon: float, cusps: list[float]) -> int:
        """Determine which Placidus house a longitude falls in.

        Returns house number (1-12).
        """
        for i in range(12):
            cusp_start = cusps[i]
            cusp_end = cusps[(i + 1) % 12]

            if cusp_start < cusp_end:
                if cusp_start <= lon < cusp_end:
                    return i + 1
            else:  # Crosses 360°/0° boundary
                if lon >= cusp_start or lon < cusp_end:
                    return i + 1

        return 1  # Fallback to 1st house

    def _calculate_ruling_planets(
        self,
        dt_utc: datetime,
        sidereal_asc: float,
        moon_lon: float,
    ) -> KpRulingPlanets:
        """Calculate the 5 ruling planets at a given moment.

        KP Ruling Planets:
        1. Ascendant sign lord
        2. Ascendant star (Nakshatra) lord
        3. Ascendant sub-lord
        4. Moon sign lord
        5. Moon star lord
        6. Moon sub-lord
        7. Day lord
        """
        asc_rashi_idx = int(sidereal_asc // 30) % 12
        asc_sign_lord = RashiCalculator.get_rashi_lord(asc_rashi_idx)
        asc_nak = NakshatraCalculator.calculate_from_longitude(sidereal_asc)
        asc_kp = KpSubLordCalculator.calculate_sublord(sidereal_asc)

        moon_rashi_idx = int(moon_lon // 30) % 12
        moon_sign_lord = RashiCalculator.get_rashi_lord(moon_rashi_idx)
        moon_nak = NakshatraCalculator.calculate_from_longitude(moon_lon)
        moon_kp = KpSubLordCalculator.calculate_sublord(moon_lon)

        # Day lord (weekday)
        day_of_week = dt_utc.weekday()  # 0=Monday, 6=Sunday
        day_lord = DAY_LORDS.get(day_of_week, "Sun")

        return KpRulingPlanets(
            moment_utc=dt_utc.isoformat(),
            ascendant_sign_lord=asc_sign_lord,
            ascendant_star_lord=asc_nak.ruler,
            ascendant_sub_lord=asc_kp.sub_lord,
            moon_sign_lord=moon_sign_lord,
            moon_star_lord=moon_nak.ruler,
            moon_sub_lord=moon_kp.sub_lord,
            day_lord=day_lord,
        )
