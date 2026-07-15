"""인수인계용: DB 엔진/세션 생성 및 요청 단위 세션 제공."""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=True)
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine, 
    class_=AsyncSession,
    expire_on_commit=False # 비동기 세션에서 greenlet 오류를 방지하기 위해 중요
)

Base = declarative_base()

async def get_db():
    """요청 단위 DB 세션 제공(의존성 주입용)."""
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
