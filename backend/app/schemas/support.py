from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.system import TicketStatus


class InquiryCreate(BaseModel):
    type: str = Field(min_length=1, max_length=50)
    content: str = Field(min_length=5, max_length=5000)
    reply_email: EmailStr


class InquiryAnswer(BaseModel):
    response: str = Field(min_length=1, max_length=5000)


class InquiryRead(BaseModel):
    id: UUID
    type: str
    subject: str
    content: str
    reply_email: Optional[str] = None
    response: Optional[str] = None
    status: TicketStatus
    sender_name: str
    sender_email: str
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
