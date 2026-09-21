"""API endpoints for Natal Chart calculations, persistence, and versioning."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.astrology.timezone import timezone_engine
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
    """Perform on-demand astronomical & astrological calculations without saving to database."""
    return service.calculate_ephemeral(req)


def format_decimal_coordinates(lat: float, lon: float) -> str:
    """Format coordinates as Decimal Coordinates with direction: e.g. 23.65° N, 88.13° E."""
    lat_dir = "N" if lat >= 0 else "S"
    lon_dir = "E" if lon >= 0 else "W"
    return f"{abs(lat):.2f}° {lat_dir}, {abs(lon):.2f}° {lon_dir}"


@router.get("/geo-search")
async def search_places(
    q: str = Query(..., min_length=2, description="Place or city name to search"),
) -> list[dict[str, Any]]:
    """Search global places/cities using OpenStreetMap Nominatim with formatted decimal coordinates."""
    url = "https://nominatim.openstreetmap.org/search"
    headers = {
        "User-Agent": "PersonalAIAstrologer/1.0 (celestial-engine@antigravity.ai)",
        "Accept": "application/json",
    }
    params = {
        "q": q,
        "format": "jsonv2",
        "limit": 6,
        "addressdetails": 1,
    }

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code != 200:
                return []
            data = resp.json()
    except Exception:
        return []

    results = []
    for item in data:
        try:
            lat = float(item["lat"])
            lon = float(item["lon"])
            name = item.get("display_name", "")
            # Clean up short name
            parts = [p.strip() for p in name.split(",") if p.strip()]
            short_name = ", ".join(parts[:3]) if len(parts) >= 3 else name
            results.append({
                "display_name": name,
                "short_name": short_name,
                "latitude": round(lat, 4),
                "longitude": round(lon, 4),
                "latitude_formatted": f"{abs(lat):.2f}° {'N' if lat >= 0 else 'S'}",
                "longitude_formatted": f"{abs(lon):.2f}° {'E' if lon >= 0 else 'W'}",
                "formatted_coordinates": format_decimal_coordinates(lat, lon),
            })
        except (KeyError, ValueError):
            continue

    return results


@router.get("/timezone-lookup")
async def lookup_timezone(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    date_str: str | None = Query(None, alias="date"),
    time_str: str | None = Query(None, alias="time"),
) -> dict[str, Any]:
    """Resolve IANA timezone and UTC offset for precise astronomical calculation."""
    tz_name = timezone_engine.find_timezone(latitude=latitude, longitude=longitude)

    # Calculate UTC offset
    from zoneinfo import ZoneInfo
    now_dt = datetime.now(timezone.utc)
    if date_str:
        try:
            from datetime import date as dt_date, time as dt_time
            d = dt_date.fromisoformat(date_str)
            t = dt_time.fromisoformat(time_str) if time_str else dt_time(12, 0)
            now_dt = datetime.combine(d, t, tzinfo=timezone.utc)
        except Exception:
            pass

    try:
        tz = ZoneInfo(tz_name)
        aware_dt = now_dt.astimezone(tz)
        utcoffset = aware_dt.utcoffset()
        offset_seconds = utcoffset.total_seconds() if utcoffset else 0
        offset_hours = round(offset_seconds / 3600.0, 2)
        sign = "+" if offset_hours >= 0 else "-"
        abs_hrs = int(abs(offset_hours))
        abs_mins = int((abs(offset_hours) - abs_hrs) * 60)
        offset_str = f"UTC{sign}{abs_hrs:02d}:{abs_mins:02d}"
    except Exception:
        offset_hours = 0.0
        offset_str = "UTC+00:00"

    return {
        "timezone": tz_name,
        "utc_offset": offset_hours,
        "offset_string": offset_str,
        "formatted_coordinates": format_decimal_coordinates(latitude, longitude),
    }


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
