from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from app.models.chat import ChatSession, ChatMessage, ChatRole
from app.schemas.chat import ChatSessionCreate, ChatMessageCreate
from app.services.rag_service import rag_service

async def create_session(
    db: AsyncSession, user_id: UUID, obj_in: ChatSessionCreate
) -> ChatSession:
    """채팅 세션 생성."""
    db_obj = ChatSession(
        user_id=user_id,
        document_id=obj_in.document_id,
        title=obj_in.title or "New Chat"
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def get_session(db: AsyncSession, session_id: UUID) -> Optional[ChatSession]:
    """세션 ID로 채팅 세션 조회."""
    result = await db.execute(select(ChatSession).filter(ChatSession.id == session_id))
    return result.scalars().first()

async def get_user_sessions(
    db: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 50
) -> List[ChatSession]:
    """사용자 기준 채팅 세션 목록 조회."""
    result = await db.execute(
        select(ChatSession)
        .filter(ChatSession.user_id == user_id)
        .order_by(desc(ChatSession.updated_at))
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def create_message(
    db: AsyncSession, session_id: UUID, obj_in: ChatMessageCreate
) -> ChatMessage:
    """채팅 메시지 저장 및 세션 갱신."""
    db_obj = ChatMessage(
        session_id=session_id,
        role=obj_in.role,
        content=obj_in.content,
        citations=obj_in.citations or [],
        model_name=obj_in.model_name,
        prompt_tokens=obj_in.prompt_tokens or 0,
        completion_tokens=obj_in.completion_tokens or 0,
    )
    db.add(db_obj)
    
    # 세션 업데이트 시간 갱신
    session = await get_session(db, session_id)
    if session:
        session.updated_at = datetime.utcnow()
        db.add(session)
        
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def get_messages(
    db: AsyncSession, session_id: UUID, skip: int = 0, limit: int = 100
) -> List[ChatMessage]:
    """채팅 메시지 목록 조회."""
    result = await db.execute(
        select(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def process_question(
    db: AsyncSession,
    session_id: UUID,
    question: str,
    user_settings: dict = None
) -> ChatMessage:
    """
    사용자 질문 처리: 저장 → 컨텍스트 검색 → 응답 생성 → 저장.
    """
    # 1. 사용자 메시지 저장
    user_msg_in = ChatMessageCreate(role=ChatRole.USER, content=question)
    await create_message(db, session_id, user_msg_in)

    # 2. 컨텍스트(대화 히스토리) 조회
    previous_messages = await get_messages(db, session_id, limit=20)
    
    # 역할 값 안전 처리 헬퍼
    def get_role_value(role):
        return role.value if hasattr(role, 'value') else role

    llm_messages = [{"role": get_role_value(msg.role), "content": msg.content} for msg in previous_messages]
    
    # 3. 세션 정보 조회(문서 연결 확인)
    session = await get_session(db, session_id)
    
    # 4. RAG 서비스 호출
    response_in = await rag_service.get_chat_completion(
        db=db,
        query=question,
        messages=llm_messages,
        document_id=session.document_id if session else None,
        user_settings=user_settings
    )
    
    # 5. 어시스턴트 메시지 저장
    return await create_message(db, session_id, response_in)
