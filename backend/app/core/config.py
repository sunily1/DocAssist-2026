"""인수인계용: 환경 변수 로딩 및 전역 설정 관리."""

import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# .env 파일을 명시적으로 로드합니다.
current_file = os.path.abspath(__file__)
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file)))), "backend", ".env")

if not os.path.exists(env_path):
    env_path = ".env"

# 수동 로딩 (폴백)
if os.path.exists(env_path):
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value
                    # print(f"디버그: 환경 변수 수동 설정: {key}")
    except Exception as e:
        pass

load_dotenv(env_path, override=True)

if not os.environ.get("OPENAI_BASE_URL", "").strip():
    os.environ.pop("OPENAI_BASE_URL", None)


class Settings(BaseSettings):
    """프로젝트 전역 설정(환경 변수 기반)."""
    PROJECT_NAME: str = "DocAssist"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    CORS_ORIGINS: str = "http://localhost:3000"
    FRONTEND_URL: str = "http://localhost:3000"

    # Password reset email
    PASSWORD_RESET_EXPIRE_MINUTES: int = 30
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_STARTTLS: bool = True
    SMTP_USE_SSL: bool = False

    # Initial administrator. Set only in the local/server .env file.
    INITIAL_ADMIN_EMAIL: str = os.getenv("INITIAL_ADMIN_EMAIL", "").strip()
    INITIAL_ADMIN_PASSWORD: str = os.getenv("INITIAL_ADMIN_PASSWORD", "")
    
    # 데이터베이스
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/docassist"

    # LLM / OpenAI-compatible API
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "").strip()
    OPENAI_CHAT_MODEL: str = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
    OPENAI_QA_MODEL: str = os.getenv("OPENAI_QA_MODEL", "gpt-4o")
    OPENAI_EMBEDDING_MODEL: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

    # Korean dictionary API
    DICTIONARY_API_KEY: str = os.getenv("DICTIONARY_API_KEY", "")
    DICTIONARY_API_URL: str = os.getenv(
        "DICTIONARY_API_URL",
        "https://kli.korean.go.kr/term/api/search.do",
    )

    model_config = SettingsConfigDict(
        case_sensitive=True,
        extra="ignore" 
    )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def smtp_configured(self) -> bool:
        return bool(self.SMTP_HOST.strip() and self.SMTP_FROM_EMAIL.strip())

settings = Settings()
