import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import UserCreate
from app.services import user_service
from app.models.user import User

@pytest.mark.asyncio
async def test_create_user(db: AsyncSession):
    user_in = UserCreate(email="service_test@example.com", password="password", name="Service Test")
    user = await user_service.create(db, user_in)
    
    assert user.email == user_in.email
    assert hasattr(user, "id")
    assert isinstance(user, User)

@pytest.mark.asyncio
async def test_get_user(db: AsyncSession):
    user_in = UserCreate(email="get_test@example.com", password="password", name="Get Test")
    created_user = await user_service.create(db, user_in)
    
    fetched_user = await user_service.get_by_email(db, created_user.email)
    assert fetched_user is not None
    assert fetched_user.id == created_user.id
    assert isinstance(fetched_user, User)


