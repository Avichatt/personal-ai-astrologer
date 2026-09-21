"""Tests for birth profiles API routes."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_birth_profile_auto_geocode(client: AsyncClient, test_user, auth_headers):
    payload = {
        "name": "Kolkata Native",
        "date_of_birth": "1995-05-10",
        "local_time": "14:35:00",
        "location_name": "Kolkata, India",
        "astrology_system": "vedic",
        "is_primary": True,
    }
    response = await client.post("/api/v1/birth-profiles", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Kolkata Native"
    assert data["latitude"] == pytest.approx(22.5726, abs=0.1)
    assert data["longitude"] == pytest.approx(88.3639, abs=0.1)
    assert data["timezone"] == "Asia/Kolkata"
    assert data["is_primary"] is True
    assert "utc_datetime" in data


@pytest.mark.asyncio
async def test_create_birth_profile_explicit_coords(client: AsyncClient, test_user, auth_headers):
    payload = {
        "name": "New York Native",
        "date_of_birth": "1990-01-15",
        "local_time": "08:30:00",
        "location_name": "New York, NY",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "timezone": "America/New_York",
        "astrology_system": "western",
    }
    response = await client.post("/api/v1/birth-profiles", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["timezone"] == "America/New_York"
    assert data["latitude"] == 40.7128
    assert data["longitude"] == -74.0060


@pytest.mark.asyncio
async def test_list_and_get_birth_profiles(client: AsyncClient, test_user, auth_headers):
    # Create two profiles
    p1 = {
        "name": "Profile 1",
        "date_of_birth": "1992-03-12",
        "local_time": "10:00:00",
        "location_name": "London, UK",
        "latitude": 51.5074,
        "longitude": -0.1278,
    }
    resp1 = await client.post("/api/v1/birth-profiles", json=p1, headers=auth_headers)
    profile_id = resp1.json()["id"]

    # List
    list_resp = await client.get("/api/v1/birth-profiles", headers=auth_headers)
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert len(items) >= 1

    # Get single
    get_resp = await client.get(f"/api/v1/birth-profiles/{profile_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Profile 1"


@pytest.mark.asyncio
async def test_update_and_delete_birth_profile(client: AsyncClient, test_user, auth_headers):
    p = {
        "name": "Original Name",
        "date_of_birth": "1988-11-20",
        "local_time": "18:45:00",
        "location_name": "Tokyo, Japan",
        "latitude": 35.6762,
        "longitude": 139.6503,
    }
    resp = await client.post("/api/v1/birth-profiles", json=p, headers=auth_headers)
    profile_id = resp.json()["id"]

    # Patch
    patch_resp = await client.patch(
        f"/api/v1/birth-profiles/{profile_id}",
        json={"name": "Renamed Profile"},
        headers=auth_headers,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["name"] == "Renamed Profile"

    # Delete
    del_resp = await client.delete(f"/api/v1/birth-profiles/{profile_id}", headers=auth_headers)
    assert del_resp.status_code == 200

    # Verify 404
    get_after = await client.get(f"/api/v1/birth-profiles/{profile_id}", headers=auth_headers)
    assert get_after.status_code == 404
