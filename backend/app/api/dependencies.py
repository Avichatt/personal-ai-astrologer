"""FastAPI dependency injection factories."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.database.models.user import User
from app.services.auth import AuthService
from app.services.user import UserService
from app.utils.security import decode_access_token

security_bearer = HTTPBearer(auto_error=False)

DatabaseDep = Annotated[AsyncSession, Depends(get_db)]


async def get_auth_service(session: DatabaseDep) -> AuthService:
    """Dependency to provide AuthService."""
    return AuthService(session)


async def get_user_service(session: DatabaseDep) -> UserService:
    """Dependency to provide UserService."""
    return UserService(session)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_bearer)],
    session: DatabaseDep,
) -> User:
    """Dependency to extract and validate current authenticated user from JWT bearer token."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token claims.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id = uuid.UUID(user_id_str)
    except (JWTError, ValueError) as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from err

    auth_service = AuthService(session)
    user = await auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deleted.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account.",
        )

    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]
