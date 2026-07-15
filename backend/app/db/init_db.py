"""인수인계용: 초기 데이터(관리자 계정) 생성 로직."""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.services import user_service
from app.schemas.user import UserCreate
from app.models.user import UserRole
from app.core import security
from app.core.config import settings

logger = logging.getLogger(__name__)

async def init_db(db: AsyncSession) -> None:
    """
    관리자 계정이 없으면 초기 생성합니다.
    """
    try:
        admin_email = settings.INITIAL_ADMIN_EMAIL
        admin_password = settings.INITIAL_ADMIN_PASSWORD

        if not admin_email or not admin_password:
            logger.warning(
                "Initial admin creation skipped. Set INITIAL_ADMIN_EMAIL and "
                "INITIAL_ADMIN_PASSWORD in backend/.env for a fresh database."
            )
            return

        if len(admin_password) < 8:
            logger.error("Initial admin password must be at least 8 characters.")
            return
        
        user = await user_service.get_by_email(db, email=admin_email)
        if not user:
            logger.info(f"Creating initial admin user: {admin_email}")
            user_in = UserCreate(
                email=admin_email,
                password=admin_password,
                name="Administrator",
                is_active=True
            )
            # 사용자 생성
            # UserCreate에 role이 없으므로 생성 후 ADMIN으로 변경
            # user_service.create는 기본 role=USER를 사용
            
            # user_service.create로 비밀번호 해싱을 처리하고
            # 생성 후 role을 수동으로 변경
            
            # 역할이 정확히 ADMIN이 되도록 수동 처리
            db_obj = await user_service.create(db, user_in)
            
            # 역할을 ADMIN으로 갱신
            db_obj.role = UserRole.ADMIN
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            
            logger.info("Admin user created successfully")
        else:
            logger.info(f"Admin user {admin_email} already exists")
            
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
