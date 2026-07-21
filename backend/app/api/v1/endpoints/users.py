from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.user import User
from app.models.system import SupportTicket
from app.schemas.support import InquiryCreate, InquiryRead
from app.schemas.user import FeedbackRead, FeedbackUpsert, PresenceRead, UserRead, UserUpdate, UserPasswordChange
from app.services import user_service
from app.services import analytics_service
from app.core import security

router = APIRouter()


def _user_inquiry_payload(ticket: SupportTicket, user: User) -> dict[str, Any]:
    return {
        "id": ticket.id,
        "type": ticket.type,
        "subject": ticket.subject,
        "content": ticket.content,
        "reply_email": ticket.reply_email,
        "response": ticket.response,
        "status": ticket.status,
        "sender_name": user.name,
        "sender_email": user.email,
        "created_at": ticket.created_at,
        "updated_at": ticket.updated_at,
        "resolved_at": ticket.resolved_at,
    }


@router.post("/me/inquiries", response_model=InquiryRead, status_code=status.HTTP_201_CREATED)
async def create_inquiry(
    inquiry_in: InquiryCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    ticket = SupportTicket(
        user_id=current_user.id,
        type=inquiry_in.type,
        subject=inquiry_in.type,
        content=inquiry_in.content,
        reply_email=str(inquiry_in.reply_email),
    )
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)
    return _user_inquiry_payload(ticket, current_user)


@router.get("/me/inquiries", response_model=list[InquiryRead])
async def read_my_inquiries(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    tickets = (
        await db.execute(
            select(SupportTicket)
            .filter(SupportTicket.user_id == current_user.id)
            .order_by(SupportTicket.created_at.desc())
        )
    ).scalars().all()
    return [_user_inquiry_payload(ticket, current_user) for ticket in tickets]


@router.post("/me/presence", response_model=PresenceRead)
async def update_presence(
    request: Request,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """현재 사용자의 실제 접속 시각과 기기 유형을 갱신합니다."""
    seen_at, device_type = await analytics_service.record_presence(
        db, current_user, request.headers.get("user-agent")
    )
    return {"last_seen_at": seen_at, "device_type": device_type}


@router.get("/me/feedback", response_model=FeedbackRead | None)
async def read_feedback(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    return await analytics_service.get_feedback(db, current_user.id)


@router.put("/me/feedback", response_model=FeedbackRead)
async def update_feedback(
    feedback_in: FeedbackUpsert,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    return await analytics_service.upsert_feedback(db, current_user.id, feedback_in.rating)

@router.get("/me", response_model=UserRead)
async def read_user_me(
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """현재 로그인 사용자 정보 조회."""
    return current_user

@router.patch("/me", response_model=UserRead)
async def update_user_me(
    *,
    db: AsyncSession = Depends(deps.get_db),
    user_in: UserUpdate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """현재 사용자 프로필/설정 수정."""
    user = await user_service.update(db, db_obj=current_user, obj_in=user_in)
    return user

@router.put("/me/password", response_model=UserRead)
async def change_password_me(
    *,
    db: AsyncSession = Depends(deps.get_db),
    password_in: UserPasswordChange,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """현재 사용자 비밀번호 변경."""
    if not security.verify_password(password_in.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="현재 비밀번호가 올바르지 않습니다.")
    
    user_in = UserUpdate(password=password_in.new_password)
    user = await user_service.update(db, db_obj=current_user, obj_in=user_in)
    return user
