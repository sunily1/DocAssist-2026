"""인수인계용: 사용자 관련 요청/응답 스키마."""

from typing import Literal, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr
from uuid import UUID

from app.models.user import UserRole

# 공통 필드
class UserBase(BaseModel):
    """사용자 기본 필드."""
    email: str
    name: Optional[str] = None
    is_active: Optional[bool] = True

# 생성 요청 필드
class UserCreate(UserBase):
    """회원가입 요청 스키마."""
    password: str

# 수정 요청 필드
class UserUpdate(BaseModel):
    """사용자 업데이트 요청 스키마."""
    name: Optional[str] = None
    password: Optional[str] = None
    profile_settings: Optional[dict] = None

class UserPasswordChange(BaseModel):
    """비밀번호 변경 요청 스키마."""
    current_password: str
    new_password: str

class UserInDBBase(UserBase):
    """DB 공통 필드 포함 스키마."""
    id: UUID
    role: UserRole
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# API 응답에 추가로 포함할 필드
class UserRead(UserInDBBase):
    """응답용 사용자 스키마."""
    profile_settings: Optional[dict] = {}


class PresenceRead(BaseModel):
    last_seen_at: datetime
    device_type: str


class FeedbackUpsert(BaseModel):
    rating: Literal["satisfied", "neutral", "dissatisfied"]


class FeedbackRead(BaseModel):
    rating: Literal["satisfied", "neutral", "dissatisfied"]
    updated_at: datetime

    class Config:
        from_attributes = True

# 토큰
class Token(BaseModel):
    """로그인 토큰 응답."""
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    """JWT Payload 파싱용."""
    sub: Optional[str] = None
