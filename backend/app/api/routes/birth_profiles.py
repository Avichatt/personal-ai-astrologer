"""Birth profiles API routes."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import CurrentUserDep, DatabaseDep
from app.schemas.birth_profile import (
    BirthProfileCreate,
    BirthProfileResponse,
    BirthProfileUpdate,
)
from app.schemas.common import SuccessResponse
from app.services.birth_profile import BirthProfileService

router = APIRouter(prefix="/birth-profiles", tags=["Birth Profiles"])


async def get_birth_profile_service(session: DatabaseDep) -> BirthProfileService:
    return BirthProfileService(session)


BirthProfileServiceDep = Annotated[BirthProfileService, Depends(get_birth_profile_service)]


@router.post("", response_model=BirthProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_birth_profile(
    current_user: CurrentUserDep,
    payload: BirthProfileCreate,
    service: BirthProfileServiceDep,
) -> BirthProfileResponse:
    """Create a new birth profile with automatic geocoding and timezone resolution."""
    return await service.create_profile(current_user.id, payload)


@router.get("", response_model=list[BirthProfileResponse], status_code=status.HTTP_200_OK)
async def list_birth_profiles(
    current_user: CurrentUserDep,
    service: BirthProfileServiceDep,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> list[BirthProfileResponse]:
    """List all birth profiles owned by the current user."""
    return await service.get_user_profiles(current_user.id, offset=offset, limit=limit)


@router.get("/{profile_id}", response_model=BirthProfileResponse, status_code=status.HTTP_200_OK)
async def get_birth_profile(
    profile_id: uuid.UUID,
    current_user: CurrentUserDep,
    service: BirthProfileServiceDep,
) -> BirthProfileResponse:
    """Get a specific birth profile by ID."""
    return await service.get_profile_by_id(current_user.id, profile_id)


@router.patch("/{profile_id}", response_model=BirthProfileResponse, status_code=status.HTTP_200_OK)
async def update_birth_profile(
    profile_id: uuid.UUID,
    current_user: CurrentUserDep,
    payload: BirthProfileUpdate,
    service: BirthProfileServiceDep,
) -> BirthProfileResponse:
    """Update a birth profile and recalculate astronomical coordinates/time if necessary."""
    return await service.update_profile(current_user.id, profile_id, payload)


@router.delete("/{profile_id}", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
async def delete_birth_profile(
    profile_id: uuid.UUID,
    current_user: CurrentUserDep,
    service: BirthProfileServiceDep,
) -> SuccessResponse:
    """Delete a birth profile."""
    await service.delete_profile(current_user.id, profile_id)
    return SuccessResponse(message="Birth profile successfully deleted.")
