"""Authentication API routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_auth_service
from app.config.settings import get_settings
from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.common import SuccessResponse
from app.services.auth import AuthService
from app.utils.rate_limiter import rate_limit

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()


@router.post(
    "/register",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(settings.rate_limit_auth))],
)
async def register(
    req: RegisterRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> dict:
    """Register a new user account."""
    user, token = await auth_service.register(req)
    return {
        "user": user.model_dump(),
        "token": token.model_dump(),
    }


@router.post(
    "/login",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(rate_limit(settings.rate_limit_auth))],
)
async def login(
    req: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> dict:
    """Authenticate and obtain JWT bearer token."""
    user, token = await auth_service.login(req)
    return {
        "user": user.model_dump(),
        "token": token.model_dump(),
    }


@router.post(
    "/logout",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
)
async def logout() -> SuccessResponse:
    """Logout current session."""
    return SuccessResponse(message="Successfully logged out.")
