from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.schemas.chat import ChatSessionCreate, ChatSessionRead, ChatMessageCreate, ChatMessageRead, ChatQuestion
from app.models.user import User
from app.services import chat_service

router = APIRouter()

@router.post("/sessions", response_model=ChatSessionRead, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_in: ChatSessionCreate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """채팅 세션 생성(문서 선택적 연결)."""
    try:
        session = await chat_service.create_session(db, current_user.id, session_in)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return session

@router.get("/sessions", response_model=List[ChatSessionRead])
async def get_sessions(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """현재 사용자 채팅 세션 목록 조회."""
    sessions = await chat_service.get_user_sessions(db, current_user.id, skip=skip, limit=limit)
    return sessions

@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageRead])
async def get_messages(
    session_id: UUID,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """채팅 세션의 메시지 목록 조회."""
    session = await chat_service.get_session(db, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Chat session not found or not authorized")
    
    messages = await chat_service.get_messages(db, session_id, skip=skip, limit=limit)
    return messages

@router.post("/sessions/{session_id}/ask", response_model=ChatMessageRead)
async def ask_question(
    session_id: UUID,
    chat_question: ChatQuestion,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """사용자 질문을 RAG 서비스로 처리하고 응답 메시지 저장."""
    # 1. 권한 확인
    session = await chat_service.get_session(db, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Chat session not found or not authorized")
    
    # 2. 질문 처리 위임
    user_settings = getattr(current_user, 'profile_settings', {})
    
    try:
        assistant_message = await chat_service.process_question(
            db=db,
            session_id=session_id,
            question=chat_question.question,
            user_settings=user_settings
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return assistant_message
