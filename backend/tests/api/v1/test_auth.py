import pytest
from httpx import AsyncClient
from app.core.config import settings

@pytest.mark.asyncio
async def test_signup(client: AsyncClient):
    # Given
    payload = {
        "email": "test@example.com",
        "password": "strongpassword",
        "name": "Test User"
    }

    # When
    response = await client.post(f"{settings.API_V1_STR}/auth/signup", json=payload)

    # Then
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == payload["email"]
    assert "id" in data
    assert "password" not in data  # Should not return password

@pytest.mark.asyncio
async def test_signup_duplicate_email(client: AsyncClient):
    # Given
    payload = {
        "email": "duplicate@example.com",
        "password": "password123",
        "name": "Duplicate User"
    }
    # First signup
    await client.post(f"{settings.API_V1_STR}/auth/signup", json=payload)

    # When (Second signup with same email)
    response = await client.post(f"{settings.API_V1_STR}/auth/signup", json=payload)

    # Then
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    # Given (Create user first)
    email = "login_test@example.com"
    password = "loginpass123"
    await client.post(f"{settings.API_V1_STR}/auth/signup", json={
        "email": email,
        "password": password,
        "name": "Login User"
    })

    # When (Login)
    login_data = {
        "username": email,
        "password": password
    }
    response = await client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)

    # Then
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

