"""Authentication service."""

from __future__ import annotations

import uuid
from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.database.models.user import User
from app.database.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.utils.security import create_access_token, hash_password, verify_password


class AuthService:
    """Authentication and user session management service."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.settings = get_settings()

    async def register(self, req: RegisterRequest) -> tuple[UserResponse, TokenResponse]:
        """Register a new user account."""
        if await self.user_repo.email_exists(req.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email address already exists.",
            )

        user = await self.user_repo.create(
            email=req.email,
            hashed_password=hash_password(req.password),
            display_name=req.display_name,
            is_active=True,
            is_verified=False,
        )
        await self.session.commit()

        token = self._create_user_token(user)
        return UserResponse.model_validate(user), token

    async def login(self, req: LoginRequest) -> tuple[UserResponse, TokenResponse]:
        """Authenticate user credentials and return access token."""
        user = await self.user_repo.get_by_email(req.email)
        if not user or not verify_password(req.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated.",
            )

        token = self._create_user_token(user)
        return UserResponse.model_validate(user), token

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        """Fetch user by ID."""
        return await self.user_repo.get_by_id(user_id)

    def _create_user_token(self, user: User) -> TokenResponse:
        """Helper to create standard access token for user."""
        expire_minutes = self.settings.jwt_access_token_expire_minutes
        access_token = create_access_token(
            subject=user.id,
            expires_delta=timedelta(minutes=expire_minutes),
            extra_claims={"email": user.email},
        )
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=expire_minutes * 60,
        )
