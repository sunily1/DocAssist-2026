from typing import Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core import security
from app.schemas.user import Token, UserCreate, UserRead
from app.services import user_service
from app.services.analytics_service import detect_device_type

router = APIRouter()

@router.post("/login", response_model=Token)
async def login(
    request: Request,
    db: AsyncSession = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """로그인 처리: 비밀번호 검증 후 JWT 발급."""
    user = await user_service.get_by_email(db, email=form_data.username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
        )
    
    # 안전한 접근(딕셔너리/객체 모두 대응)
    if isinstance(user, dict):
        password_hash = user.get("password_hash")
        user_id = user.get("id")
        is_active = user.get("is_active")
    else:
        password_hash = user.password_hash
        user_id = user.id
        is_active = user.is_active

    if not security.verify_password(form_data.password, password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
        )
    elif not is_active:
        raise HTTPException(status_code=400, detail="비활성화된 계정입니다.")
    
    if not isinstance(user, dict):
        now = datetime.now(timezone.utc)
        user.last_login_at = now
        user.last_seen_at = now
        user.last_device_type = detect_device_type(request.headers.get("user-agent"))
        db.add(user)
        await db.commit()

    access_token = security.create_access_token(subject=user_id)
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }

@router.post("/signup", response_model=UserRead)
async def signup(
    *,
    db: AsyncSession = Depends(deps.get_db),
    user_in: UserCreate,
) -> Any:
    """회원가입 처리: 이메일 중복 체크 후 사용자 생성."""
    user = await user_service.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    user = await user_service.create(db, obj_in=user_in)
    return user
