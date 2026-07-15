import pytest
import uuid
import os
from httpx import AsyncClient
from app.core.config import settings

@pytest.mark.asyncio
async def test_upload_document(client: AsyncClient, db):
    # 1. Create User & Login
    email = "doc_test@example.com"
    password = "password"
    await client.post(f"{settings.API_V1_STR}/auth/signup", json={
        "email": email,
        "password": password,
        "name": "Doc User"
    })
    
    login_res = await client.post(f"{settings.API_V1_STR}/auth/login", data={
        "username": email,
        "password": password
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Upload File
    files = {"file": ("test.txt", b"test content", "text/plain")}
    response = await client.post(
        f"{settings.API_V1_STR}/documents/upload",
        headers=headers,
        files=files
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "test.txt"
    assert data["original_filename"] == "test.txt"
    assert "id" in data
    
    # 3. Get Document List
    response = await client.get(
        f"{settings.API_V1_STR}/documents/",
        headers=headers
    )
    assert response.status_code == 200
    data_list = response.json()
    assert len(data_list) > 0
    assert data_list[0]["title"] == "test.txt"

    # 4. Delete Document
    doc_id = data["id"]
    response = await client.delete(
        f"{settings.API_V1_STR}/documents/{doc_id}",
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["deleted_at"] is not None


