from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash

async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """이메일로 사용자 조회."""
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalars().first()

async def get(db: AsyncSession, id: UUID) -> Optional[User]:
    """ID로 사용자 조회."""
    result = await db.execute(select(User).filter(User.id == id))
    return result.scalars().first()

async def create(db: AsyncSession, obj_in: UserCreate) -> User:
    """새 사용자 생성(비밀번호 해싱 포함)."""
    db_obj = User(
        email=obj_in.email,
        name=obj_in.name,
        password_hash=get_password_hash(obj_in.password),
        is_active=True
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def update(db: AsyncSession, db_obj: User, obj_in: UserUpdate) -> User:
    """사용자 정보 수정(비밀번호 변경 포함)."""
    update_data = obj_in.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["password_hash"] = get_password_hash(update_data.pop("password"))
    
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj
