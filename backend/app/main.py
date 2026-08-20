import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router
from app.core.logging_config import setup_logging
from app.db.session import SessionLocal
from app.db.init_db import init_db

# 인수인계용: FastAPI 앱 엔트리포인트 (라우터/미들웨어/수명주기 초기화 담당)

# 로깅 설정 초기화
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 DB 초기화 등 공통 작업을 처리."""
    if len(settings.SECRET_KEY) < 32:
        raise RuntimeError("SECRET_KEY must be configured with at least 32 characters")
    # 시작 시 초기화
    logger.info("Initializing database...")
    async with SessionLocal() as db:
        await init_db(db)
    yield
    # 종료 시 정리
    logger.info("Shutting down...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 예외 처리기
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """전역 예외를 로깅하고 500 응답으로 통일."""
    # 500 에러 발생 시 로그에 스택 트레이스 기록
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error. Please check server logs."},
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    logger.info("Root endpoint called")
    return {"message": "Welcome to DocAssist API"}
