import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.session import Base

if TYPE_CHECKING:
    from .document import Document
    from .chat import ChatSession, PinnedMessage
    from .system import SupportTicket

class UserRole(str, Enum):
    """사용자 권한 구분(일반/관리자)."""
    USER = "USER"
    ADMIN = "ADMIN"

class User(Base):
    """사용자 기본 정보 및 프로필 설정."""
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.USER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    profile_settings: Mapped[dict] = mapped_column(JSONB, default=lambda: {})
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_device_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 관계
    term_agreements: Mapped[List["TermAgreement"]] = relationship("TermAgreement", back_populates="user", cascade="all, delete-orphan")
    documents: Mapped[List["Document"]] = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    chat_sessions: Mapped[List["ChatSession"]] = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    support_tickets: Mapped[List["SupportTicket"]] = relationship("SupportTicket", back_populates="user")
    pinned_messages: Mapped[List["PinnedMessage"]] = relationship("PinnedMessage", back_populates="user", cascade="all, delete-orphan")
    service_feedback: Mapped[Optional["ServiceFeedback"]] = relationship(
        "ServiceFeedback", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    # 참고: 필요 시 아래 관계를 활성화 가능
    # support_tickets: Mapped[List["SupportTicket"]] = relationship("SupportTicket", back_populates="user")
    # pinned_messages: Mapped[List["PinnedMessage"]] = relationship("PinnedMessage", back_populates="user", cascade="all, delete-orphan")

class PasswordReset(Base):
    """비밀번호 재설정 토큰 관리."""
    __tablename__ = "password_resets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    token: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class TermAgreement(Base):
    """약관 동의 이력 관리."""
    __tablename__ = "term_agreements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    term_version: Mapped[str] = mapped_column(String(20), nullable=False)
    agreed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="term_agreements")


class ServiceFeedback(Base):
    """관리자 만족도 통계에 사용하는 사용자별 최신 평가."""
    __tablename__ = "service_feedback"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    rating: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="service_feedback")
