"""인수인계용: 로깅 설정(콘솔/파일 출력 포맷)."""

import logging
import sys
from pathlib import Path
from app.core.config import settings

# 로그 저장 디렉토리
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# 로그 포맷
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logging():
    """전역 로깅 설정 적용."""
    # 기본 로거 설정
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        handlers=[
            # 콘솔 출력
            logging.StreamHandler(sys.stdout),
            # 파일 출력(로테이팅 없음)
            logging.FileHandler(LOG_DIR / "app.log", encoding="utf-8")
        ]
    )

    # 타사 라이브러리 로그 레벨 조정
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    logger = logging.getLogger("app")
    logger.info("Logging configuration setup complete.")
