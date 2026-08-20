from typing import Any
from datetime import datetime, timedelta, timezone
import hashlib
import logging
import secrets
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import PasswordReset
from app.schemas.user import (
    MessageRead,
    PasswordResetConfirm,
    PasswordResetRequest,
    Token,
    UserCreate,
    UserRead,
)
from app.services import user_service
from app.services.analytics_service import detect_device_type
from app.services.email_service import send_password_reset_email

router = APIRouter()
logger = logging.getLogger(__name__)

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
            detail="이미 가입된 이메일입니다.",
        )
    user = await user_service.create(db, obj_in=user_in)
    return user


@router.post("/forgot-password", response_model=MessageRead)
async def forgot_password(
    payload: PasswordResetRequest,
    db: AsyncSession = Depends(deps.get_db),
) -> MessageRead:
    """Issue a one-time reset token and deliver it through configured SMTP."""
    if not settings.smtp_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="비밀번호 재설정 메일 기능이 아직 설정되지 않았습니다. 관리자에게 문의해 주세요.",
        )

    user = await user_service.get_by_email(db, email=str(payload.email))
    generic = MessageRead(message="가입된 이메일이라면 비밀번호 재설정 링크를 전송했습니다.")
    if not user:
        return generic

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES
    )
    await db.execute(delete(PasswordReset).where(PasswordReset.email == user.email))
    db.add(PasswordReset(email=user.email, token=token_hash, expires_at=expires_at))
    await db.commit()

    reset_url = (
        f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?token="
        f"{quote(raw_token, safe='')}"
    )
    try:
        await send_password_reset_email(user.email, reset_url)
    except Exception as exc:
        await db.execute(delete(PasswordReset).where(PasswordReset.token == token_hash))
        await db.commit()
        logger.exception("Password reset email delivery failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="재설정 메일을 보내지 못했습니다. 잠시 후 다시 시도해 주세요.",
        ) from exc
    return generic


@router.post("/reset-password", response_model=MessageRead)
async def reset_password(
    payload: PasswordResetConfirm,
    db: AsyncSession = Depends(deps.get_db),
) -> MessageRead:
    """Consume a one-time reset token and replace the account password."""
    token_hash = hashlib.sha256(payload.token.encode("utf-8")).hexdigest()
    record = (
        await db.execute(select(PasswordReset).where(PasswordReset.token == token_hash))
    ).scalar_one_or_none()
    now = datetime.now(timezone.utc)
    expires_at = record.expires_at if record else None
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if not record or not expires_at or expires_at <= now:
        if record:
            await db.delete(record)
            await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="재설정 링크가 유효하지 않거나 만료되었습니다.",
        )

    user = await user_service.get_by_email(db, email=record.email)
    if not user or not user.is_active:
        await db.delete(record)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="재설정 링크가 유효하지 않거나 만료되었습니다.",
        )

    user.password_hash = security.get_password_hash(payload.password)
    db.add(user)
    await db.execute(delete(PasswordReset).where(PasswordReset.email == record.email))
    await db.commit()
    return MessageRead(message="비밀번호가 변경되었습니다. 새 비밀번호로 로그인해 주세요.")
