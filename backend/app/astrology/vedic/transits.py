"""Vedic Transit (Gochar) and Sade Sati calculation engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime

from app.astrology.ephemeris import EphemerisService
from app.config.constants import RASHI_NAMES, AstrologySystem, Ayanamsa, Planet, Sign


@dataclass(frozen=True)
class SadeSatiInfo:
    """Detailed Sade Sati and Saturn transit status."""

    is_sade_sati_active: bool
    phase_name: str | None  # "Rising (12th)", "Peak (1st / Janma Shani)", "Setting (2nd)", or None
    is_ashtama_shani: bool  # Saturn in 8th from Moon
    is_ardha_ashtama_shani: bool  # Saturn in 4th from Moon
    saturn_transit_rashi: str
    natal_moon_rashi: str
    description: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class VedicGocharItem:
    """Individual planet's transit placement relative to Natal Moon and Lagna."""

    graha_name: str
    transit_rashi_index: int
    transit_rashi_name: str
    transit_longitude: float
    house_from_moon: int
    house_from_lagna: int
    is_favorable_from_moon: bool  # Classical Gochar favorable houses for each planet


@dataclass(frozen=True)
class VedicTransitResult:
    """Comprehensive Gochar analysis."""

    transit_datetime_utc: datetime
    ayanamsa_used: str
    transiting_grahas: list[VedicGocharItem]
    sade_sati: SadeSatiInfo

    def to_dict(self) -> dict:
        return {
            "transit_datetime_utc": self.transit_datetime_utc.isoformat(),
            "ayanamsa_used": self.ayanamsa_used,
            "transiting_grahas": [asdict(g) for g in self.transiting_grahas],
            "sade_sati": self.sade_sati.to_dict(),
        }


# Classical Favorable Houses from Moon (Gochar Phala)
FAVORABLE_GOCHAR_HOUSES: dict[str, set[int]] = {
    "Sun": {3, 6, 10, 11},
    "Moon": {1, 3, 6, 7, 10, 11},
    "Mars": {3, 6, 11},
    "Mercury": {2, 4, 6, 8, 10, 11},
    "Jupiter": {2, 5, 7, 9, 11},
    "Venus": {1, 2, 3, 4, 5, 8, 9, 11, 12},
    "Saturn": {3, 6, 11},
    "Rahu": {3, 6, 10, 11},
    "Ketu": {3, 6, 9, 11},
}


class VedicTransitCalculator:
    """Calculates Sidereal Gochar transits, house placements from Janma Rashi, and Sade Sati."""

    def __init__(self, ephemeris: EphemerisService | None = None) -> None:
        self.ephemeris = ephemeris or EphemerisService()

    def calculate_gochar(
        self,
        natal_moon_longitude: float,
        natal_lagna_longitude: float,
        transit_utc: datetime,
        ayanamsa: Ayanamsa = Ayanamsa.LAHIRI,
    ) -> VedicTransitResult:
        """
        Compute real-time Vedic Gochar transits relative to natal Moon and Ascendant.
        """
        transit_utc = (
            transit_utc.replace(tzinfo=UTC)
            if transit_utc.tzinfo is None
            else transit_utc.astimezone(UTC)
        )
        jd = self.ephemeris.datetime_to_julian_day(transit_utc)

        natal_moon_rashi_idx = int(natal_moon_longitude // 30) % 12
        natal_lagna_rashi_idx = int(natal_lagna_longitude // 30) % 12

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

        transit_positions = [
            self.ephemeris.calculate_planet(
                jd=jd,
                planet=p,
                system=AstrologySystem.VEDIC,
                ayanamsa=ayanamsa,
            )
            for p in planets_to_calc
        ]

        # Calculate Gochar items
        gochar_items: list[VedicGocharItem] = []
        saturn_pos = None

        for tp in transit_positions:
            p_name = "Rahu" if tp.name in ("North Node", "True Node") else tp.name
            t_rashi_idx = tp.sign_index
            h_from_moon = ((t_rashi_idx - natal_moon_rashi_idx) % 12) + 1
            h_from_lagna = ((t_rashi_idx - natal_lagna_rashi_idx) % 12) + 1

            fav_houses = FAVORABLE_GOCHAR_HOUSES.get(p_name, {3, 6, 11})
            is_fav = h_from_moon in fav_houses

            if p_name == "Saturn":
                saturn_pos = tp

            gochar_items.append(
                VedicGocharItem(
                    graha_name=p_name,
                    transit_rashi_index=t_rashi_idx,
                    transit_rashi_name=RASHI_NAMES[Sign(t_rashi_idx)],
                    transit_longitude=round(tp.longitude, 4),
                    house_from_moon=h_from_moon,
                    house_from_lagna=h_from_lagna,
                    is_favorable_from_moon=is_fav,
                )
            )

        # Sade Sati Evaluation
        saturn_rashi_idx = saturn_pos.sign_index if saturn_pos else 0
        diff_from_moon = ((saturn_rashi_idx - natal_moon_rashi_idx) % 12) + 1

        is_sade_sati = diff_from_moon in (12, 1, 2)
        is_ashtama = diff_from_moon == 8
        is_ardha = diff_from_moon == 4

        phase_name = None
        if diff_from_moon == 12:
            phase_name = "Rising Phase (12th from Moon)"
            desc = "Saturn is transiting the 12th house from natal Moon — beginning of Sade Sati bringing introspection, inner restructuring, and preparation."
        elif diff_from_moon == 1:
            phase_name = "Peak Phase (Janma Shani / 1st from Moon)"
            desc = "Saturn is transiting directly over natal Moon — core phase of Sade Sati emphasizing discipline, emotional maturity, and deep karmic realignment."
        elif diff_from_moon == 2:
            phase_name = "Setting Phase (2nd from Moon)"
            desc = "Saturn is transiting the 2nd house from natal Moon — final phase of Sade Sati focusing on family stability, financial consolidation, and enduring lessons."
        elif is_ashtama:
            phase_name = "Ashtama Shani (8th from Moon)"
            desc = "Saturn in the 8th house from Moon triggers profound transformative shifts and life reassessment."
        elif is_ardha:
            phase_name = "Ardha-Ashtama Shani (4th from Moon)"
            desc = "Saturn in the 4th house from Moon influences home, comfort, and inner peace."
        else:
            desc = "Saturn is not currently in Sade Sati or adverse transit from the natal Moon."

        sade_sati = SadeSatiInfo(
            is_sade_sati_active=is_sade_sati,
            phase_name=phase_name,
            is_ashtama_shani=is_ashtama,
            is_ardha_ashtama_shani=is_ardha,
            saturn_transit_rashi=RASHI_NAMES[Sign(saturn_rashi_idx)],
            natal_moon_rashi=RASHI_NAMES[Sign(natal_moon_rashi_idx)],
            description=desc,
        )

        return VedicTransitResult(
            transit_datetime_utc=transit_utc,
            ayanamsa_used=ayanamsa.value,
            transiting_grahas=gochar_items,
            sade_sati=sade_sati,
        )
