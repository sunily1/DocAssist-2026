import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.models.document import DocStatus, DocumentEmbedding, DocumentJob, Document
import os
import asyncio

@pytest.mark.asyncio
async def test_document_upload_and_processing(client: AsyncClient, db: AsyncSession):
    # 1. Signup & Login
    email = "proc_test@example.com"
    password = "password"
    await client.post(f"{settings.API_V1_STR}/auth/signup", json={
        "email": email,
        "password": password,
        "name": "Process User"
    })
    login_res = await client.post(f"{settings.API_V1_STR}/auth/login", data={
        "username": email,
        "password": password
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Upload File
    file_content = "This is a test document for embedding generation. It should be processed by the background task."
    files = {"file": ("test_process.txt", file_content.encode("utf-8"), "text/plain")}
    
    response = await client.post(
        f"{settings.API_V1_STR}/documents/upload",
        headers=headers,
        files=files
    )
    assert response.status_code == 201
    doc_id = response.json()["id"]

    # 3. Wait for background processing
    # In a real async test environment, background tasks scheduled by FastAPI 
    # might not run immediately or guaranteed within the test function scope unless we manage the loop.
    # However, Starlette's TestClient usually runs background tasks. 
    # AsyncClient serves the app, so background tasks are added to the loop.
    
    print(f"Waiting for document {doc_id} processing...")
    
    max_retries = 15
    processed = False
    
    for _ in range(max_retries):
        await asyncio.sleep(1) # Wait 1 sec
        
        # We need to query the DB to check status.
        # Since background task commits to DB in a separate transaction,
        # and our test 'db' session is in a transaction, we might need to expire/refresh to see changes.
        # But 'db' session here is used for setup. Let's create a new query or just use the session.
        # To see committed data from other transactions in READ COMMITTED, we just need to execute a new query.
        # If the session has already queried this data, it might be cached in identity map.
        
        # Using a fresh session or direct execution might be safer for checking external side effects.
        # But let's try with provided db session.
        
        result = await db.execute(select(Document).filter(Document.id == doc_id))
        doc = result.scalars().first()
        await db.refresh(doc) # Force refresh from DB
        
        print(f"Current Status: {doc.status}")
        
        if doc.status == DocStatus.DONE:
            processed = True
            break
        if doc.status == DocStatus.FAILED:
            print("Processing Failed!")
            # Check job error
            j_res = await db.execute(select(DocumentJob).filter(DocumentJob.document_id == doc_id))
            job = j_res.scalars().first()
            if job:
                print(f"Error: {job.error_message}")
            break
            
    assert processed, "Document processing did not complete in time"
    
    # 4. Verify Embeddings
    result = await db.execute(select(DocumentEmbedding).filter(DocumentEmbedding.document_id == doc_id))
    embeddings = result.scalars().all()
    
    assert len(embeddings) > 0
    assert len(embeddings[0].embedding) == 1536


