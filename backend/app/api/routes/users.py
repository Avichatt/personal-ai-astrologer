"""Users management API routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import CurrentUserDep, get_user_service
from app.schemas.common import SuccessResponse
from app.schemas.user import UserDetailResponse, UserPasswordChange, UserProfileUpdate
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserDetailResponse, status_code=status.HTTP_200_OK)
async def get_current_user_profile(
    current_user: CurrentUserDep,
) -> UserDetailResponse:
    """Get current authenticated user profile."""
    return UserDetailResponse.model_validate(current_user)


@router.patch("/me", response_model=UserDetailResponse, status_code=status.HTTP_200_OK)
async def update_current_user_profile(
    current_user: CurrentUserDep,
    update_data: UserProfileUpdate,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserDetailResponse:
    """Update current authenticated user profile."""
    return await user_service.update_profile(current_user.id, update_data)


@router.post("/me/change-password", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
async def change_password(
    current_user: CurrentUserDep,
    data: UserPasswordChange,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> SuccessResponse:
    """Change current authenticated user password."""
    await user_service.change_password(current_user.id, data)
    return SuccessResponse(message="Password successfully changed.")


@router.delete("/me", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
async def delete_current_user_account(
    current_user: CurrentUserDep,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> SuccessResponse:
    """Delete current authenticated user account."""
    await user_service.delete_account(current_user.id)
    return SuccessResponse(message="Account successfully deleted.")
