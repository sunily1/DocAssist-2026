"""인수인계용: 채팅/세션 관련 스키마."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

from app.models.chat import ChatRole

# 메시지 스키마
class ChatMessageBase(BaseModel):
    """채팅 메시지 공통 필드."""
    role: ChatRole
    content: str
    citations: Optional[List[Dict[str, Any]]] = []

class ChatMessageCreate(ChatMessageBase):
    """채팅 메시지 생성 스키마."""
    model_name: Optional[str] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0

class ChatMessageRead(ChatMessageBase):
    """채팅 메시지 응답 스키마."""
    id: UUID
    session_id: UUID
    created_at: datetime
    model_name: Optional[str] = None

    class Config:
        from_attributes = True

# 세션 스키마
class ChatSessionBase(BaseModel):
    """채팅 세션 공통 필드."""
    title: Optional[str] = None
    document_id: Optional[UUID] = None

class ChatSessionCreate(ChatSessionBase):
    """채팅 세션 생성 스키마."""
    pass

class ChatSessionRead(ChatSessionBase):
    """채팅 세션 응답 스키마."""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    
    # 선택: 마지막 메시지 또는 메시지 리스트 포함 가능
    # messages: List[ChatMessageRead] = []

    class Config:
        from_attributes = True

# 질문 요청 스키마
class ChatQuestion(BaseModel):
    """질문 요청 스키마."""
    question: str
    model: str = "gpt-4o"
