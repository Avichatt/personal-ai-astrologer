"""User request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserProfileUpdate(BaseModel):
    """User profile update request."""

    display_name: str | None = Field(None, min_length=1, max_length=100)


class UserPasswordChange(BaseModel):
    """Password change request."""

    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class UserDetailResponse(BaseModel):
    """Detailed user profile response."""

    id: uuid.UUID
    email: EmailStr
    display_name: str | None
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
