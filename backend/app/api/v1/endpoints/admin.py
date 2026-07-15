from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from app.services.health_service import get_llm_status
from app.services.dictionary_service import get_dictionary_status

from app.api import deps
from app.models.user import User, UserRole
from app.models.document import Document
from app.schemas.user import UserRead
from app.api.deps import get_current_admin_user

router = APIRouter()

@router.get("/metrics")
async def get_system_metrics(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """관리자 대시보드 지표 조회."""
    user_count = int(await db.scalar(text("SELECT count(*) FROM users")) or 0)
    signup_count = int(await db.scalar(text("SELECT count(*) FROM users WHERE created_at >= date_trunc('day', now())")) or 0)
    today_login_count = int(await db.scalar(text("SELECT count(*) FROM users WHERE last_login_at >= date_trunc('day', now())")) or 0)
    active_user_count = int(await db.scalar(text("SELECT count(*) FROM users WHERE last_seen_at >= now() - interval '2 minutes'")) or 0)
    doc_count = int(await db.scalar(text("SELECT count(*) FROM documents WHERE deleted_at IS NULL")) or 0)
    today_upload_count = int(await db.scalar(text("SELECT count(*) FROM documents WHERE deleted_at IS NULL AND created_at >= date_trunc('day', now())")) or 0)
    queue_count = int(await db.scalar(text("SELECT count(*) FROM documents WHERE deleted_at IS NULL AND status::text IN ('QUEUED', 'PROCESSING')")) or 0)
    glossary_count = int(
        await db.scalar(
            text(
                "SELECT count(*) FROM glossary_terms gt "
                "JOIN documents d ON d.id = gt.document_id "
                "WHERE d.deleted_at IS NULL"
            )
        )
        or 0
    )
    glossary_today_count = int(
        await db.scalar(
            text(
                "SELECT count(*) FROM glossary_terms gt "
                "JOIN documents d ON d.id = gt.document_id "
                "WHERE d.deleted_at IS NULL AND gt.created_at >= date_trunc('day', now())"
            )
        )
        or 0
    )
    glossary_pinned_count = int(
        await db.scalar(
            text(
                "SELECT count(*) FROM glossary_terms gt "
                "JOIN documents d ON d.id = gt.document_id "
                "WHERE d.deleted_at IS NULL AND gt.is_pinned = true"
            )
        )
        or 0
    )
    text_convert_count = int(await db.scalar(text("SELECT count(*) FROM system_logs WHERE level = 'METRIC' AND message = 'text_convert'")) or 0)
    file_convert_count = doc_count
    chat_count = int(await db.scalar(text("SELECT count(*) FROM chat_messages WHERE role::text IN ('USER', 'user')")) or 0)
    chat_today_count = int(
        await db.scalar(
            text(
                "SELECT count(*) FROM chat_messages "
                "WHERE role::text IN ('USER', 'user') AND created_at >= date_trunc('day', now())"
            )
        )
        or 0
    )

    satisfaction_rows = (
        await db.execute(text("SELECT rating, count(*) FROM service_feedback GROUP BY rating"))
    ).all()
    satisfaction_counts = {str(row[0]): int(row[1]) for row in satisfaction_rows}

    device_rows = (
        await db.execute(
            text(
                "SELECT last_device_type, count(*) FROM users "
                "WHERE last_device_type IS NOT NULL GROUP BY last_device_type"
            )
        )
    ).all()
    device_counts = {str(row[0]): int(row[1]) for row in device_rows}

    llm_status = await get_llm_status()
    dictionary_status = await get_dictionary_status()

    return {
        "users": user_count,
        "docs": doc_count,
        "queue": queue_count,
        "qaToday": chat_today_count,
        "signups": signup_count,
        "loginsToday": today_login_count,
        "activeUsers": active_user_count,
        "uploadsToday": today_upload_count,
        "glossaryTerms": glossary_count,
        "glossaryTermsToday": glossary_today_count,
        "glossaryPinned": glossary_pinned_count,
        "serviceUsage": [
            {"label": "텍스트 변환", "value": text_convert_count},
            {"label": "파일 변환", "value": file_convert_count},
            {"label": "챗봇", "value": chat_count},
            {"label": "용어집", "value": glossary_count},
        ],
        "satisfaction": [
            {"label": "만족", "value": satisfaction_counts.get("satisfied", 0), "color": "#5b8cff"},
            {"label": "보통", "value": satisfaction_counts.get("neutral", 0), "color": "#21c7b7"},
            {"label": "불만", "value": satisfaction_counts.get("dissatisfied", 0), "color": "#fb7185"},
        ],
        "devices": [
            {"label": "데스크톱", "value": device_counts.get("desktop", 0), "color": "#5b8cff"},
            {"label": "모바일", "value": device_counts.get("mobile", 0), "color": "#21c7b7"},
            {"label": "태블릿", "value": device_counts.get("tablet", 0), "color": "#fbbf24"},
        ],
        "apiStatus": {
            "backend": {"status": "ok", "label": "백엔드", "message": "정상"},
            "db": {"status": "ok", "label": "DB", "message": "정상"},
            "openai": llm_status,
            "dictionary": dictionary_status,
        },
    }

@router.get("/users", response_model=List[UserRead])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """관리자용 전체 사용자 목록 조회."""
    result = await db.execute(select(User).offset(skip).limit(limit).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return users

# 관리자 문서 목록은 DocumentRead 스키마를 재사용
from app.schemas.document import DocumentRead as DocumentSchema

@router.get("/documents", response_model=List[DocumentSchema])
async def get_all_documents(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """관리자용 전체 문서 목록 조회."""
    result = await db.execute(
        select(Document)
        .filter(Document.deleted_at == None)
        .offset(skip)
        .limit(limit)
        .order_by(Document.created_at.desc())
    )
    documents = result.scalars().all()
    return documents
