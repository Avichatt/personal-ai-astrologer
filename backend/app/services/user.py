"""User service for profile management and account settings."""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.user import UserRepository
from app.schemas.user import UserDetailResponse, UserPasswordChange, UserProfileUpdate
from app.utils.security import hash_password, verify_password


class UserService:
    """User profile and account operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)

    async def get_profile(self, user_id: uuid.UUID) -> UserDetailResponse:
        """Fetch user profile details."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        return UserDetailResponse.model_validate(user)

    async def update_profile(
        self, user_id: uuid.UUID, update_data: UserProfileUpdate
    ) -> UserDetailResponse:
        """Update user profile fields."""
        fields_to_update = update_data.model_dump(exclude_unset=True)
        if not fields_to_update:
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
            return UserDetailResponse.model_validate(user)

        user = await self.user_repo.update(user_id, **fields_to_update)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        await self.session.commit()
        return UserDetailResponse.model_validate(user)

    async def change_password(self, user_id: uuid.UUID, data: UserPasswordChange) -> None:
        """Change user password after verifying current password."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        if not verify_password(data.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password.",
            )

        new_hash = hash_password(data.new_password)
        await self.user_repo.update(user_id, hashed_password=new_hash)
        await self.session.commit()

    async def delete_account(self, user_id: uuid.UUID) -> bool:
        """Soft deactivate or hard delete user account."""
        deleted = await self.user_repo.delete(user_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        await self.session.commit()
        return True
