import pytest
import asyncio
import os
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from app.db.session import Base, get_db
# Import models to ensure they are registered with Base.metadata
from app.models import (
    User, PasswordReset, TermAgreement, ServiceFeedback,
    Document, DocumentJob, DocumentAnalysis, GlossaryTerm, DocumentEmbedding,
    ChatSession, ChatMessage, PinnedMessage,
    SupportTicket, AccessPolicy, SystemSetting, SystemLog
)
from app.main import app
from app.core.config import settings

def _test_database_url() -> str:
    configured = os.getenv("TEST_DATABASE_URL", "").strip()
    if configured:
        return configured

    runtime_url = make_url(settings.DATABASE_URL)
    database = runtime_url.database or "docassist"
    return runtime_url.set(database=f"{database}_test").render_as_string(hide_password=False)


# Integration tests must never drop tables from the runtime database.
TEST_DATABASE_URL = _test_database_url()
if make_url(TEST_DATABASE_URL) == make_url(settings.DATABASE_URL):
    raise RuntimeError("TEST_DATABASE_URL must be different from DATABASE_URL")

@pytest.fixture(scope="function")
async def db_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    # await conn.run_sync(Base.metadata.drop_all) # Optional
    await engine.dispose()

@pytest.fixture(scope="function")
async def db(db_engine) -> AsyncGenerator[AsyncSession, None]:
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, expire_on_commit=False, bind=db_engine, class_=AsyncSession
    )
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()

@pytest.fixture(scope="function")
async def client(db) -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[get_db] = lambda: db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    
    app.dependency_overrides.clear()
