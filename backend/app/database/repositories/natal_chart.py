"""Repository for NatalChart database operations."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import select

from app.database.models.natal_chart import NatalChart
from app.database.repositories.base import BaseRepository


class NatalChartRepository(BaseRepository[NatalChart]):
    """Repository handling CRUD operations for NatalChart entities."""

    model = NatalChart

    async def get_by_user_and_id(
        self,
        user_id: uuid.UUID,
        chart_id: uuid.UUID,
    ) -> NatalChart | None:
        """Fetch chart guaranteeing user ownership."""
        stmt = select(NatalChart).where(
            NatalChart.id == chart_id,
            NatalChart.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_profile_id(
        self,
        user_id: uuid.UUID,
        birth_profile_id: uuid.UUID,
    ) -> Sequence[NatalChart]:
        """Fetch all charts generated for a specific birth profile."""
        stmt = (
            select(NatalChart)
            .where(
                NatalChart.user_id == user_id,
                NatalChart.birth_profile_id == birth_profile_id,
            )
            .order_by(NatalChart.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_latest_chart(
        self,
        user_id: uuid.UUID,
        birth_profile_id: uuid.UUID,
        astrology_system: str,
    ) -> NatalChart | None:
        """Get latest calculated chart for profile in a given astrology system."""
        stmt = (
            select(NatalChart)
            .where(
                NatalChart.user_id == user_id,
                NatalChart.birth_profile_id == birth_profile_id,
                NatalChart.astrology_system == astrology_system,
            )
            .order_by(NatalChart.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
