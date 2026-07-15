import pytest
import uuid
from httpx import AsyncClient
from app.core.config import settings

@pytest.mark.asyncio
async def test_chat_flow(client: AsyncClient, db):
    # 1. Create User & Login
    email = "chat_test@example.com"
    password = "password"
    await client.post(f"{settings.API_V1_STR}/auth/signup", json={
        "email": email,
        "password": password,
        "name": "Chat User"
    })
    
    login_res = await client.post(f"{settings.API_V1_STR}/auth/login", data={
        "username": email,
        "password": password
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Chat Session
    response = await client.post(
        f"{settings.API_V1_STR}/chat/sessions",
        headers=headers,
        json={"title": "Test Chat"}
    )
    assert response.status_code == 200
    session_data = response.json()
    session_id = session_data["id"]
    assert session_data["title"] == "Test Chat"

    # 3. Ask Question (Mocking OpenAI would be better, but we test the flow)
    # We skip actual OpenAI call in test if possible, or expect it to fail/work depending on env
    # For now, let's assume it works or handle error gracefully in service
    
    # Mocking openai in rag_service or just testing session retrieval for now
    response = await client.get(
        f"{settings.API_V1_STR}/chat/sessions/{session_id}/messages",
        headers=headers
    )
    assert response.status_code == 200
    messages = response.json()
    assert isinstance(messages, list)
    assert len(messages) == 0

    # 4. Get User Sessions
    response = await client.get(
        f"{settings.API_V1_STR}/chat/sessions",
        headers=headers
    )
    assert response.status_code == 200
    sessions = response.json()
    assert len(sessions) > 0
    assert sessions[0]["id"] == session_id


