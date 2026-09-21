"""Vimshottari Dasha calculation engine for Vedic Astrology."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.astrology.vedic.nakshatras import NakshatraCalculator
from app.config.constants import (
    VIMSHOTTARI_ORDER,
    VIMSHOTTARI_PERIODS,
)

DAYS_PER_YEAR = 365.2422


@dataclass(frozen=True)
class MahadashaPeriod:
    """A single Mahadasha timeline segment."""

    lord: str
    start_date: datetime
    end_date: datetime
    duration_years: float


class VimshottariDashaEngine:
    """Computes exact balance of birth dasha and the full 120-year sequence of Mahadashas."""

    @classmethod
    def calculate_mahadashas(
        cls,
        moon_sidereal_longitude: float,
        birth_datetime_utc: datetime,
        cycle_count: int = 1,
    ) -> list[MahadashaPeriod]:
        """
        Generate full sequence of Mahadashas starting from the birth moment.
        """
        birth_dt = (
            birth_datetime_utc.replace(tzinfo=UTC)
            if birth_datetime_utc.tzinfo is None
            else birth_datetime_utc.astimezone(UTC)
        )

        nak_info = NakshatraCalculator.calculate_from_longitude(moon_sidereal_longitude)
        first_lord = nak_info.ruler
        elapsed_fraction = nak_info.elapsed_fraction

        first_lord_total_years = VIMSHOTTARI_PERIODS[first_lord]
        balance_years = (1.0 - elapsed_fraction) * first_lord_total_years

        start_index = VIMSHOTTARI_ORDER.index(first_lord)
        total_lords = len(VIMSHOTTARI_ORDER)

        mahadashas: list[MahadashaPeriod] = []
        current_time = birth_dt

        # First dasha (balance period)
        first_dasha_end = current_time + timedelta(days=balance_years * DAYS_PER_YEAR)
        mahadashas.append(
            MahadashaPeriod(
                lord=first_lord,
                start_date=current_time,
                end_date=first_dasha_end,
                duration_years=round(balance_years, 4),
            )
        )
        current_time = first_dasha_end

        # Subsequent dashas across the cycle
        total_dashas_to_generate = (total_lords * cycle_count) - 1
        for step in range(1, total_dashas_to_generate + 1):
            lord_idx = (start_index + step) % total_lords
            lord_name = VIMSHOTTARI_ORDER[lord_idx]
            duration = VIMSHOTTARI_PERIODS[lord_name]
            end_time = current_time + timedelta(days=duration * DAYS_PER_YEAR)

            mahadashas.append(
                MahadashaPeriod(
                    lord=lord_name,
                    start_date=current_time,
                    end_date=end_time,
                    duration_years=round(duration, 4),
                )
            )
            current_time = end_time

        return mahadashas
