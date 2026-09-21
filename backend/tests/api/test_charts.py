"""Tests for Natal Chart API endpoints (/api/v1/charts/*)."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_calculate_ephemeral_chart(client: AsyncClient):
    payload = {
        "utc_datetime": "1995-05-10T09:05:00Z",
        "latitude": 22.5726,
        "longitude": 88.3639,
        "astrology_system": "western",
        "house_system": "placidus",
    }
    response = await client.post("/api/v1/charts/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["system"] == "western"
    assert data["sun_sign"] == "Taurus"
    assert data["ascendant_sign"] == "Libra"


@pytest.mark.asyncio
async def test_create_and_get_chart_for_profile(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    # 1. Create a birth profile first
    profile_payload = {
        "name": "Arjun Chart Test",
        "date_of_birth": "1995-05-10",
        "local_time": "14:35:00",
        "location_name": "Kolkata, India",
        "latitude": 22.5726,
        "longitude": 88.3639,
        "timezone": "Asia/Kolkata",
    }
    p_resp = await client.post(
        "/api/v1/birth-profiles",
        json=profile_payload,
        headers=auth_headers,
    )
    assert p_resp.status_code == 201
    profile_id = p_resp.json()["id"]

    # 2. Save a Vedic chart for this profile
    chart_payload = {
        "birth_profile_id": profile_id,
        "astrology_system": "vedic",
        "house_system": "whole_sign",
        "ayanamsa": "lahiri",
    }
    c_resp = await client.post(
        "/api/v1/charts",
        json=chart_payload,
        headers=auth_headers,
    )
    assert c_resp.status_code == 201
    chart_data = c_resp.json()
    chart_id = chart_data["id"]
    assert chart_data["astrology_system"] == "vedic"
    assert chart_data["birth_profile_id"] == profile_id

    # 3. Get chart by ID
    get_resp = await client.get(f"/api/v1/charts/{chart_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == chart_id

    # 4. List charts by profile
    list_resp = await client.get(f"/api/v1/charts/profile/{profile_id}", headers=auth_headers)
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] >= 1
