"""KP (Krishnamurti Paddhati) sub-lord calculation engine.

Implements the 249-position KP sub-lord table by dividing each of the 27 Nakshatras
(each 13°20') into 9 sub-lords proportional to Vimshottari Dasha periods.
Each sub-lord is further divided into 9 sub-sub-lords for finest event timing.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.astrology.vedic.nakshatras import NakshatraCalculator, NakshatraInfo
from app.config.constants import (
    KP_SUB_PERIODS,
    NAKSHATRA_SPAN_DEGREES,
    VIMSHOTTARI_ORDER,
    VIMSHOTTARI_PERIODS,
    VIMSHOTTARI_TOTAL_YEARS,
)


@dataclass(frozen=True)
class KpSubLordInfo:
    """KP sub-lord and sub-sub-lord data for a sidereal longitude."""

    nakshatra: NakshatraInfo
    star_lord: str  # Nakshatra ruler (same as nakshatra.ruler)
    sub_lord: str  # Sub-lord within the Nakshatra
    sub_sub_lord: str  # Sub-sub-lord within the sub-lord division
    sub_lord_index: int  # 0-8 position within the Nakshatra
    sub_sub_lord_index: int  # 0-8 position within the sub-lord
    sub_start_deg: float  # Absolute start degree of the sub-lord division
    sub_end_deg: float  # Absolute end degree of the sub-lord division
    sub_sub_start_deg: float  # Absolute start degree of the sub-sub-lord
    sub_sub_end_deg: float  # Absolute end degree of the sub-sub-lord
    kp_number: int = 1  # Position 1-249 in KP sub-lord table

    @property
    def sub_lord_span_deg(self) -> float:
        """Total span of the sub-lord in degrees."""
        return self.sub_end_deg - self.sub_start_deg


class KpSubLordCalculator:
    """Calculates KP star-lord, sub-lord, and sub-sub-lord from sidereal longitude.

    The KP system divides each Nakshatra (13°20') into 9 sub-lords in the order
    of Vimshottari Dasha sequence, starting from the Nakshatra ruler. Each sub-lord
    span is proportional to its Vimshottari Dasha period (e.g. Venus gets 20/120 of 13°20').

    Similarly, each sub-lord division is further divided into 9 sub-sub-lords following
    the same Vimshottari sequence starting from the sub-lord itself.
    """

    @classmethod
    def calculate_sublord(cls, sidereal_longitude: float) -> KpSubLordInfo:
        """Compute full KP sub-lord chain for a given sidereal longitude [0, 360)."""
        lon = sidereal_longitude % 360.0

        # Get Nakshatra info (star lord, pada, etc.)
        nak_info = NakshatraCalculator.calculate_from_longitude(lon)
        star_lord = nak_info.ruler

        # Degree within this Nakshatra [0, 13.3333...)
        deg_in_nak = nak_info.longitude_in_nakshatra

        # Absolute start of this Nakshatra
        nak_start_deg = nak_info.index * NAKSHATRA_SPAN_DEGREES

        # Find sub-lord: iterate through Vimshottari sequence starting from star lord
        star_lord_idx = VIMSHOTTARI_ORDER.index(star_lord)
        sub_lord, sub_lord_index, sub_start_in_nak, sub_end_in_nak = cls._find_sub_lord(
            deg_in_nak, star_lord_idx
        )

        # Degree within the sub-lord division
        deg_in_sub = deg_in_nak - sub_start_in_nak
        sub_span = sub_end_in_nak - sub_start_in_nak

        # Find sub-sub-lord: same logic within the sub-lord span
        sub_lord_idx_in_order = VIMSHOTTARI_ORDER.index(sub_lord)
        sub_sub_lord, sub_sub_index, ss_start_in_sub, ss_end_in_sub = cls._find_sub_sub_lord(
            deg_in_sub, sub_lord_idx_in_order, sub_span
        )

        return KpSubLordInfo(
            nakshatra=nak_info,
            star_lord=star_lord,
            sub_lord=sub_lord,
            sub_sub_lord=sub_sub_lord,
            sub_lord_index=sub_lord_index,
            sub_sub_lord_index=sub_sub_index,
            sub_start_deg=round(nak_start_deg + sub_start_in_nak, 6),
            sub_end_deg=round(nak_start_deg + sub_end_in_nak, 6),
            sub_sub_start_deg=round(nak_start_deg + sub_start_in_nak + ss_start_in_sub, 6),
            sub_sub_end_deg=round(nak_start_deg + sub_start_in_nak + ss_end_in_sub, 6),
            kp_number=(nak_info.index * 9) + sub_lord_index + 1,
        )

    @classmethod
    def _find_sub_lord(
        cls,
        deg_in_nak: float,
        star_lord_order_idx: int,
    ) -> tuple[str, int, float, float]:
        """Find which sub-lord division contains the given degree within a Nakshatra.

        Returns: (sub_lord_name, sub_index, sub_start_in_nak, sub_end_in_nak)
        """
        total_lords = len(VIMSHOTTARI_ORDER)
        cumulative = 0.0

        for i in range(total_lords):
            lord_idx = (star_lord_order_idx + i) % total_lords
            lord_name = VIMSHOTTARI_ORDER[lord_idx]
            sub_span = KP_SUB_PERIODS[lord_name]
            next_cumulative = cumulative + sub_span

            if deg_in_nak < next_cumulative or i == total_lords - 1:
                return lord_name, i, cumulative, next_cumulative

            cumulative = next_cumulative

        # Fallback (should never reach)
        last_lord = VIMSHOTTARI_ORDER[star_lord_order_idx]
        return last_lord, 0, 0.0, KP_SUB_PERIODS[last_lord]

    @classmethod
    def _find_sub_sub_lord(
        cls,
        deg_in_sub: float,
        sub_lord_order_idx: int,
        sub_span: float,
    ) -> tuple[str, int, float, float]:
        """Find which sub-sub-lord division contains the given degree within a sub-lord.

        The sub-lord span is divided into 9 sub-sub-lords proportional to Vimshottari
        periods, starting from the sub-lord itself.

        Returns: (sub_sub_lord_name, sub_sub_index, ss_start_in_sub, ss_end_in_sub)
        """
        total_lords = len(VIMSHOTTARI_ORDER)
        cumulative = 0.0

        for i in range(total_lords):
            lord_idx = (sub_lord_order_idx + i) % total_lords
            lord_name = VIMSHOTTARI_ORDER[lord_idx]
            # Sub-sub span is proportional to Vimshottari period within the sub-lord span
            ss_span = (VIMSHOTTARI_PERIODS[lord_name] / VIMSHOTTARI_TOTAL_YEARS) * sub_span
            next_cumulative = cumulative + ss_span

            if deg_in_sub < next_cumulative or i == total_lords - 1:
                return lord_name, i, cumulative, next_cumulative

            cumulative = next_cumulative

        # Fallback
        last_lord = VIMSHOTTARI_ORDER[sub_lord_order_idx]
        return last_lord, 0, 0.0, sub_span * VIMSHOTTARI_PERIODS[last_lord] / VIMSHOTTARI_TOTAL_YEARS

    @classmethod
    def get_kp_number(cls, sidereal_longitude: float) -> int:
        """Get the KP number (1-249) for a given sidereal longitude.

        The 249 KP numbers represent each unique Star-Lord + Sub-Lord combination
        across the full 360° zodiac.
        """
        lon = sidereal_longitude % 360.0
        nak_info = NakshatraCalculator.calculate_from_longitude(lon)
        star_lord_idx = VIMSHOTTARI_ORDER.index(nak_info.ruler)

        # Find sub-lord index within this Nakshatra
        deg_in_nak = nak_info.longitude_in_nakshatra
        _, sub_index, _, _ = cls._find_sub_lord(deg_in_nak, star_lord_idx)

        # KP number = (nakshatra_index * 9) + sub_index + 1
        return (nak_info.index * 9) + sub_index + 1
