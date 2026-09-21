"""Antardasha (Bhukti) and Pratyantardasha sub-period calculations and active dasha lookup."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.astrology.vedic.dashas import MahadashaPeriod, VimshottariDashaEngine
from app.config.constants import (
    VIMSHOTTARI_ORDER,
    VIMSHOTTARI_PERIODS,
    VIMSHOTTARI_TOTAL_YEARS,
)

DAYS_PER_YEAR = 365.2422


@dataclass(frozen=True)
class DashaPeriod:
    """Detailed multi-level Dasha node."""

    mahadasha_lord: str
    antardasha_lord: str
    pratyantardasha_lord: str | None
    start_date: datetime
    end_date: datetime
    duration_days: float

    def to_dict(self) -> dict:
        return {
            "mahadasha_lord": self.mahadasha_lord,
            "antardasha_lord": self.antardasha_lord,
            "pratyantardasha_lord": self.pratyantardasha_lord,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "duration_days": round(self.duration_days, 2),
        }


@dataclass(frozen=True)
class ActiveDashaInfo:
    """Currently operating Dasha hierarchy for a target moment."""

    target_datetime_utc: datetime
    mahadasha: str
    antardasha: str
    pratyantardasha: str
    mahadasha_start: datetime
    mahadasha_end: datetime
    antardasha_start: datetime
    antardasha_end: datetime
    pratyantardasha_start: datetime
    pratyantardasha_end: datetime

    def to_dict(self) -> dict:
        return {
            "target_datetime_utc": self.target_datetime_utc.isoformat(),
            "mahadasha": self.mahadasha,
            "antardasha": self.antardasha,
            "pratyantardasha": self.pratyantardasha,
            "mahadasha_start": self.mahadasha_start.isoformat(),
            "mahadasha_end": self.mahadasha_end.isoformat(),
            "antardasha_start": self.antardasha_start.isoformat(),
            "antardasha_end": self.antardasha_end.isoformat(),
            "pratyantardasha_start": self.pratyantardasha_start.isoformat(),
            "pratyantardasha_end": self.pratyantardasha_end.isoformat(),
        }


class DashaTreeBuilder:
    """Builds nested Vimshottari Dasha periods down to Antardasha and Pratyantardasha."""

    @classmethod
    def calculate_antardashas(cls, maha: MahadashaPeriod) -> list[DashaPeriod]:
        """
        Generate all 9 Antardashas (Bhuktis) inside a Mahadasha.
        The sub-periods start with the Mahadasha lord itself.
        """
        m_lord = maha.lord
        m_idx = VIMSHOTTARI_ORDER.index(m_lord)
        total_lords = len(VIMSHOTTARI_ORDER)

        # Fraction = actual duration / standard full duration for this lord
        full_m_years = VIMSHOTTARI_PERIODS[m_lord]
        actual_m_years = (maha.end_date - maha.start_date).total_seconds() / (
            DAYS_PER_YEAR * 86400.0
        )
        scale = actual_m_years / full_m_years

        antardashas: list[DashaPeriod] = []
        curr_time = maha.start_date

        for step in range(total_lords):
            a_idx = (m_idx + step) % total_lords
            a_lord = VIMSHOTTARI_ORDER[a_idx]
            a_years = (full_m_years * VIMSHOTTARI_PERIODS[a_lord]) / VIMSHOTTARI_TOTAL_YEARS
            actual_a_years = a_years * scale
            end_time = curr_time + timedelta(days=actual_a_years * DAYS_PER_YEAR)

            # Cap precisely at Mahadasha boundary on last step
            if step == total_lords - 1 or end_time > maha.end_date:
                end_time = maha.end_date

            duration_days = (end_time - curr_time).total_seconds() / 86400.0
            antardashas.append(
                DashaPeriod(
                    mahadasha_lord=m_lord,
                    antardasha_lord=a_lord,
                    pratyantardasha_lord=None,
                    start_date=curr_time,
                    end_date=end_time,
                    duration_days=duration_days,
                )
            )
            curr_time = end_time

        return antardashas

    @classmethod
    def calculate_pratyantardashas(cls, antar: DashaPeriod) -> list[DashaPeriod]:
        """
        Generate all 9 Pratyantardashas inside an Antardasha.
        """
        m_lord = antar.mahadasha_lord
        a_lord = antar.antardasha_lord
        a_idx = VIMSHOTTARI_ORDER.index(a_lord)
        total_lords = len(VIMSHOTTARI_ORDER)
        total_a_days = (antar.end_date - antar.start_date).total_seconds() / 86400.0

        pratyantardashas: list[DashaPeriod] = []
        curr_time = antar.start_date

        for step in range(total_lords):
            p_idx = (a_idx + step) % total_lords
            p_lord = VIMSHOTTARI_ORDER[p_idx]
            p_years = VIMSHOTTARI_PERIODS[p_lord]
            # Standard ratio = p_years / 120
            p_days = total_a_days * (p_years / VIMSHOTTARI_TOTAL_YEARS)
            end_time = curr_time + timedelta(days=p_days)

            if step == total_lords - 1 or end_time > antar.end_date:
                end_time = antar.end_date

            pratyantardashas.append(
                DashaPeriod(
                    mahadasha_lord=m_lord,
                    antardasha_lord=a_lord,
                    pratyantardasha_lord=p_lord,
                    start_date=curr_time,
                    end_date=end_time,
                    duration_days=(end_time - curr_time).total_seconds() / 86400.0,
                )
            )
            curr_time = end_time

        return pratyantardashas

    @classmethod
    def find_active_dasha(
        cls,
        moon_sidereal_lon: float,
        birth_utc: datetime,
        target_utc: datetime,
    ) -> ActiveDashaInfo:
        """
        Find currently active Mahadasha, Antardasha, and Pratyantardasha for any target date.
        """
        birth_utc = (
            birth_utc.replace(tzinfo=UTC) if birth_utc.tzinfo is None else birth_utc.astimezone(UTC)
        )
        target_utc = (
            target_utc.replace(tzinfo=UTC)
            if target_utc.tzinfo is None
            else target_utc.astimezone(UTC)
        )

        mahadashas = VimshottariDashaEngine.calculate_mahadashas(
            moon_sidereal_longitude=moon_sidereal_lon,
            birth_datetime_utc=birth_utc,
            cycle_count=2,  # Cover up to 240 years
        )

        active_maha = next(
            (m for m in mahadashas if m.start_date <= target_utc < m.end_date),
            mahadashas[0],
        )

        antardashas = cls.calculate_antardashas(active_maha)
        active_antar = next(
            (a for a in antardashas if a.start_date <= target_utc < a.end_date),
            antardashas[0],
        )

        pratyantardashas = cls.calculate_pratyantardashas(active_antar)
        active_prat = next(
            (p for p in pratyantardashas if p.start_date <= target_utc < p.end_date),
            pratyantardashas[0],
        )

        return ActiveDashaInfo(
            target_datetime_utc=target_utc,
            mahadasha=active_maha.lord,
            antardasha=active_antar.antardasha_lord,
            pratyantardasha=active_prat.pratyantardasha_lord or active_antar.antardasha_lord,
            mahadasha_start=active_maha.start_date,
            mahadasha_end=active_maha.end_date,
            antardasha_start=active_antar.start_date,
            antardasha_end=active_antar.end_date,
            pratyantardasha_start=active_prat.start_date,
            pratyantardasha_end=active_prat.end_date,
        )
