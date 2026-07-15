from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, documents, chat, admin, dictionary

api_router = APIRouter()

# 인수인계용: v1 라우터 묶음 (서비스 도메인별 엔드포인트 등록)
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(dictionary.router, prefix="/dictionary", tags=["dictionary"])
