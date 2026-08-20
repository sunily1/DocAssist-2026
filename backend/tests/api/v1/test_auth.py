import pytest
from urllib.parse import parse_qs, urlparse
from httpx import AsyncClient
from app.api.v1.endpoints import auth as auth_endpoints
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
    assert response.json()["detail"] == "이미 가입된 이메일입니다."

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


@pytest.mark.asyncio
async def test_password_reset_uses_emailed_one_time_token(client: AsyncClient, monkeypatch):
    email = "password-reset@example.com"
    old_password = "old-password-123"
    new_password = "new-password-456"
    await client.post(
        f"{settings.API_V1_STR}/auth/signup",
        json={"email": email, "password": old_password, "name": "Reset User"},
    )

    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", "no-reply@example.com")
    captured: dict[str, str] = {}

    async def fake_send(recipient: str, reset_url: str) -> None:
        captured["recipient"] = recipient
        captured["url"] = reset_url

    monkeypatch.setattr(auth_endpoints, "send_password_reset_email", fake_send)
    request_response = await client.post(
        f"{settings.API_V1_STR}/auth/forgot-password",
        json={"email": email},
    )

    assert request_response.status_code == 200
    assert captured["recipient"] == email
    token = parse_qs(urlparse(captured["url"]).query)["token"][0]
    reset_response = await client.post(
        f"{settings.API_V1_STR}/auth/reset-password",
        json={"token": token, "password": new_password},
    )
    assert reset_response.status_code == 200

    old_login = await client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": email, "password": old_password},
    )
    new_login = await client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": email, "password": new_password},
    )
    reused_token = await client.post(
        f"{settings.API_V1_STR}/auth/reset-password",
        json={"token": token, "password": "another-password-789"},
    )

    assert old_login.status_code == 400
    assert new_login.status_code == 200
    assert reused_token.status_code == 400
