"""API endpoints for Natal Chart calculations, persistence, and versioning."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.database.models.user import User
from app.schemas.chart import (
    ChartCreateRequest,
    ChartListResponse,
    ChartRecalculateRequest,
    EphemeralCalculateRequest,
    NatalChartResponse,
)
from app.services.chart import ChartService

router = APIRouter(prefix="/charts", tags=["Natal Charts"])


def get_chart_service(session: Annotated[AsyncSession, Depends(get_db)]) -> ChartService:
    return ChartService(session=session)


@router.post("/calculate", response_model=dict[str, Any])
async def calculate_ephemeral_chart(
    req: EphemeralCalculateRequest,
    service: Annotated[ChartService, Depends(get_chart_service)],
) -> dict[str, Any]:
    """
    Perform on-demand astronomical & astrological calculations without saving to database.
    Open to authenticated and unauthenticated exploratory requests.
    """
    return service.calculate_ephemeral(req)


@router.post("", response_model=NatalChartResponse, status_code=status.HTTP_201_CREATED)
async def create_and_save_chart(
    req: ChartCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ChartService, Depends(get_chart_service)],
) -> NatalChartResponse:
    """Calculate and persist a new Natal Chart linked to a user's Birth Profile."""
    try:
        chart = await service.create_chart_for_profile(
            user_id=current_user.id,
            req=req,
        )
        return NatalChartResponse.model_validate(chart)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/{chart_id}", response_model=NatalChartResponse)
async def get_chart_by_id(
    chart_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ChartService, Depends(get_chart_service)],
) -> NatalChartResponse:
    """Retrieve a saved Natal Chart by ID with strict ownership verification."""
    chart = await service.get_chart(user_id=current_user.id, chart_id=chart_id)
    if not chart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Natal chart {chart_id} not found",
        )
    return NatalChartResponse.model_validate(chart)


@router.get("/profile/{profile_id}", response_model=ChartListResponse)
async def list_charts_for_birth_profile(
    profile_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ChartService, Depends(get_chart_service)],
) -> ChartListResponse:
    """List all calculated charts (Western, Vedic, different ayanamshas) for a birth profile."""
    charts = await service.list_charts_for_profile(
        user_id=current_user.id,
        profile_id=profile_id,
    )
    items = [NatalChartResponse.model_validate(c) for c in charts]
    return ChartListResponse(items=items, total=len(items))


@router.post("/{chart_id}/recalculate", response_model=NatalChartResponse)
async def recalculate_chart(
    chart_id: uuid.UUID,
    req: ChartRecalculateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ChartService, Depends(get_chart_service)],
) -> NatalChartResponse:
    """Recalculate a saved chart with upgraded engine version or different house system."""
    try:
        chart = await service.recalculate_chart(
            user_id=current_user.id,
            chart_id=chart_id,
            req=req,
        )
        return NatalChartResponse.model_validate(chart)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
