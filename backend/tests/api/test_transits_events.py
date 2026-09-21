"""Tests for Transits and Astro Events API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_current_sky_transits(client: AsyncClient):
    payload = {
        "target_datetime_utc": "2024-06-01T12:00:00Z",
        "ayanamsa": "lahiri",
    }
    response = await client.post("/api/v1/transits/current", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "western" in data
    assert "vedic" in data


@pytest.mark.asyncio
async def test_upcoming_events_api(client: AsyncClient):
    payload = {
        "start_datetime_utc": "2024-01-01T00:00:00Z",
        "days": 45,
        "min_score": 50.0,
    }
    response = await client.post("/api/v1/events/upcoming", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["items"][0]["score"] >= 50.0
