"""Tests for user profile management API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_current_user_profile(client: AsyncClient, test_user, auth_headers):
    response = await client.get("/api/v1/users/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["display_name"] == test_user.display_name


@pytest.mark.asyncio
async def test_get_current_user_unauthorized(client: AsyncClient):
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_user_profile(client: AsyncClient, test_user, auth_headers):
    payload = {"display_name": "Updated Name"}
    response = await client.patch("/api/v1/users/me", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["display_name"] == "Updated Name"


@pytest.mark.asyncio
async def test_change_password(client: AsyncClient, test_user, auth_headers):
    payload = {
        "current_password": "SecurePassword123!",
        "new_password": "BrandNewPassword456!",
    }
    response = await client.post(
        "/api/v1/users/me/change-password",
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 200

    # Verify login with new password
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "BrandNewPassword456!"},
    )
    assert login_resp.status_code == 200


@pytest.mark.asyncio
async def test_delete_user_account(client: AsyncClient, test_user, auth_headers):
    response = await client.delete("/api/v1/users/me", headers=auth_headers)
    assert response.status_code == 200

    # Subsequent request should fail
    subsequent = await client.get("/api/v1/users/me", headers=auth_headers)
    assert subsequent.status_code == 401
