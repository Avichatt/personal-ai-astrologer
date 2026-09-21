"""Generic async CRUD repository base class."""

from __future__ import annotations

import uuid
from typing import Any, TypeVar

from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository[ModelT: Base]:
    """Generic async CRUD repository.

    Subclass and set `model` to the ORM model class.
    """

    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, **kwargs: Any) -> ModelT:
        """Create a new record."""
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def get_by_id(self, record_id: uuid.UUID) -> ModelT | None:
        """Get a record by its UUID primary key."""
        return await self.session.get(self.model, record_id)

    async def get_all(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[ModelT]:
        """Get all records with pagination."""
        stmt = select(self.model).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, record_id: uuid.UUID, **kwargs: Any) -> ModelT | None:
        """Update a record by ID."""
        stmt = (
            sa_update(self.model)
            .where(self.model.id == record_id)  # type: ignore[attr-defined]
            .values(**kwargs)
            .returning(self.model)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        row = result.scalar_one_or_none()
        return row

    async def delete(self, record_id: uuid.UUID) -> bool:
        """Delete a record by ID. Returns True if deleted."""
        stmt = (
            sa_delete(self.model).where(self.model.id == record_id)  # type: ignore[attr-defined]
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0  # type: ignore[union-attr]
