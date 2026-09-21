"""Birth profile repository."""

from __future__ import annotations

import uuid

from sqlalchemy import select, update

from app.database.models.birth_profile import BirthProfile
from app.database.repositories.base import BaseRepository


class BirthProfileRepository(BaseRepository[BirthProfile]):
    """Repository for BirthProfile model operations."""

    model = BirthProfile

    async def get_by_user_and_id(
        self,
        user_id: uuid.UUID,
        profile_id: uuid.UUID,
    ) -> BirthProfile | None:
        """Fetch a birth profile ensuring user ownership."""
        stmt = select(BirthProfile).where(
            BirthProfile.id == profile_id,
            BirthProfile.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_id(
        self,
        user_id: uuid.UUID,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[BirthProfile]:
        """Fetch all birth profiles owned by a user."""
        stmt = (
            select(BirthProfile)
            .where(BirthProfile.user_id == user_id)
            .order_by(BirthProfile.is_primary.desc(), BirthProfile.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_primary_by_user_id(self, user_id: uuid.UUID) -> BirthProfile | None:
        """Fetch user's primary birth profile."""
        stmt = select(BirthProfile).where(
            BirthProfile.user_id == user_id,
            BirthProfile.is_primary.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def clear_primary(self, user_id: uuid.UUID) -> None:
        """Reset is_primary flag on all user profiles."""
        stmt = update(BirthProfile).where(BirthProfile.user_id == user_id).values(is_primary=False)
        await self.session.execute(stmt)
