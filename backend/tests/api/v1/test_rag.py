import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.models.document import Document, DocStatus, DocumentJob
from app.models.chat import ChatSession
import os

@pytest.mark.asyncio
async def test_rag_flow(client: AsyncClient, db: AsyncSession):
    # 1. Signup & Login
    email = "rag_test@example.com"
    password = "password"
    await client.post(f"{settings.API_V1_STR}/auth/signup", json={
        "email": email,
        "password": password,
        "name": "RAG User"
    })
    login_res = await client.post(f"{settings.API_V1_STR}/auth/login", data={
        "username": email,
        "password": password
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Upload Document with specific knowledge
    # Using a fake fact to verify RAG is working (Context > General Knowledge)
    fake_fact = "The capital of the Moon is Armstrong City."
    file_content = f"Important fact: {fake_fact} This is a document about lunar geography."
    
    files = {"file": ("moon_info.txt", file_content.encode("utf-8"), "text/plain")}
    
    upload_res = await client.post(
        f"{settings.API_V1_STR}/documents/upload",
        headers=headers,
        files=files
    )
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]

    # 3. Wait for processing (Polling)
    print(f"Waiting for document {doc_id} to be processed...")
    max_retries = 20
    processed = False
    for _ in range(max_retries):
        await asyncio.sleep(1)
        # Check status via API or DB
        # API is better for integration test
        doc_res = await client.get(f"{settings.API_V1_STR}/documents/{doc_id}", headers=headers)
        if doc_res.json()["status"] == DocStatus.DONE:
            processed = True
            break
        if doc_res.json()["status"] == DocStatus.FAILED:
            pytest.fail("Document processing failed")
            
    assert processed, "Document processing timeout"

    # 4. Create Chat Session linked to the document
    session_res = await client.post(
        f"{settings.API_V1_STR}/chat/sessions",
        headers=headers,
        json={"title": "Moon Chat", "document_id": doc_id}
    )
    assert session_res.status_code == 201
    session_id = session_res.json()["id"]

    # 5. Ask Question
    question = "What is the capital of the Moon?"
    print(f"Asking: {question}")
    
    ask_res = await client.post(
        f"{settings.API_V1_STR}/chat/sessions/{session_id}/ask",
        headers=headers,
        json={"question": question}
    )
    assert ask_res.status_code == 200
    answer = ask_res.json()
    
    print(f"AI Answer: {answer['content']}")
    
    # 6. Verify Answer contains the specific knowledge
    assert "Armstrong City" in answer["content"], "RAG failed to retrieve specific info from document"


