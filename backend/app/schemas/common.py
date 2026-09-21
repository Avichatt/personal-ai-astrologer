"""Common response schemas used across all API endpoints."""

from __future__ import annotations

import uuid
from typing import Any, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Structured error detail."""

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    request_id: str | None = Field(None, description="Request tracking ID")


class ErrorResponse(BaseModel):
    """Consistent error response envelope."""

    error: ErrorDetail


class SuccessResponse(BaseModel):
    """Generic success response."""

    success: bool = True
    message: str = "Operation completed successfully"


class PaginatedResponse[T](BaseModel):
    """Paginated response wrapper."""

    items: list[T]
    total: int
    offset: int
    limit: int
    has_more: bool


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str
    environment: str


class IDResponse(BaseModel):
    """Response containing just an ID (e.g., after creation)."""

    id: uuid.UUID


def make_error(code: str, message: str, request_id: str | None = None) -> dict[str, Any]:
    """Helper to build an ErrorResponse dict for FastAPI responses."""
    return {
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id,
        }
    }
