"""Tests for Horoscope Analysis API endpoints (/api/v1/analysis/*)."""

from datetime import UTC, datetime
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_horoscope_direct_endpoint(client: AsyncClient):
    payload = {
        "name": "Arjun",
        "utc_datetime": "1995-05-10T09:05:00Z",
        "latitude": 22.5726,
        "longitude": 88.3639,
        "target_date": "2026-08-01T00:00:00Z",
        "focus": "career",
        "system": "vedic",
        "ayanamsa": "lahiri",
    }
    response = await client.post("/api/v1/analysis/horoscope", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["name"] == "Arjun"
    assert data["focus"] == "career"
    assert data["system"] == "vedic"
    assert len(data["sections"]) >= 3
    assert len(data["timeline"]) >= 2
    assert "◆ 10th House (Career House) Analysis" in data["formatted_reading"]
    assert "Parashari rule:" in data["formatted_reading"]
    assert "◆ Why Delay Happening?" in data["formatted_reading"]
    assert "Exact Career Rise Timeline" in data["formatted_reading"]


@pytest.mark.asyncio
async def test_horoscope_profile_endpoint(client: AsyncClient, auth_headers: dict[str, str]):
    # 1. Create a profile
    profile_payload = {
        "name": "Priya Sharma",
        "date_of_birth": "1998-11-20",
        "local_time": "08:15:00",
        "location_name": "Delhi, India",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "timezone": "Asia/Kolkata",
    }
    p_resp = await client.post(
        "/api/v1/birth-profiles",
        json=profile_payload,
        headers=auth_headers,
    )
    assert p_resp.status_code == 201
    profile_id = p_resp.json()["id"]

    # 2. Call profile analysis endpoint
    analysis_payload = {
        "birth_profile_id": profile_id,
        "target_date": "2026-08-01T00:00:00Z",
        "focus": "career",
        "system": "vedic",
    }
    a_resp = await client.post(
        "/api/v1/analysis/profile",
        json=analysis_payload,
        headers=auth_headers,
    )
    assert a_resp.status_code == 200
    data = a_resp.json()
    assert data["name"] == "Priya Sharma"
    assert "◆ 10th House" in data["formatted_reading"]


@pytest.mark.asyncio
async def test_life_blueprint_endpoint(client: AsyncClient):
    payload = {
        "name": "Karan Malhotra",
        "utc_datetime": "1992-08-15T06:30:00Z",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "target_date": "2026-08-01T00:00:00Z",
        "system": "vedic",
    }
    response = await client.post("/api/v1/analysis/life-blueprint", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["name"] == "Karan Malhotra"
    assert data["focus"] == "life_blueprint"
    assert len(data["life_stages"]) == 5
    assert len(data["gemstone_recommendations"]) >= 3
    assert len(data["spiritual_remedies"]) >= 4
    assert "◆ Birth Chart Foundation & Technical Matrix" in data["formatted_reading"]
    assert "◆ Whole-Life Journey: Birth to Death (5 Chronological Stages)" in data["formatted_reading"]
    assert "◆ Gemstone Prescription (Ratna Chikitsa)" in data["formatted_reading"]
    assert "◆ Spiritual & Practical Remedies (Upayas)" in data["formatted_reading"]

