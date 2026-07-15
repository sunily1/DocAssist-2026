"""실제 접속 정보와 사용자 만족도 기록을 처리합니다."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import ServiceFeedback, User


def detect_device_type(user_agent: str | None) -> str:
    value = (user_agent or "").lower()
    if any(token in value for token in ("ipad", "tablet", "kindle", "silk/")):
        return "tablet"
    if any(token in value for token in ("iphone", "ipod", "android", "mobile", "windows phone")):
        return "mobile"
    return "desktop"


async def record_presence(db: AsyncSession, user: User, user_agent: str | None) -> tuple[datetime, str]:
    now = datetime.now(timezone.utc)
    device_type = detect_device_type(user_agent)
    user.last_seen_at = now
    user.last_device_type = device_type
    db.add(user)
    await db.commit()
    return now, device_type


async def upsert_feedback(db: AsyncSession, user_id, rating: str) -> ServiceFeedback:
    result = await db.execute(select(ServiceFeedback).filter(ServiceFeedback.user_id == user_id))
    feedback = result.scalars().first()
    if feedback:
        feedback.rating = rating
    else:
        feedback = ServiceFeedback(user_id=user_id, rating=rating)
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)
    return feedback


async def get_feedback(db: AsyncSession, user_id) -> ServiceFeedback | None:
    result = await db.execute(select(ServiceFeedback).filter(ServiceFeedback.user_id == user_id))
    return result.scalars().first()
