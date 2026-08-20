"""관리자 대시보드용 외부 API 상태를 짧게 캐시해 확인합니다."""

import time

import httpx

from app.core.config import settings
from app.services.easy_converter import has_valid_openai_key


_llm_cache: tuple[float, dict[str, str]] | None = None


async def get_llm_status() -> dict[str, str]:
    global _llm_cache

    now = time.monotonic()
    if _llm_cache and now - _llm_cache[0] < 300:
        return _llm_cache[1]

    key = (settings.OPENAI_API_KEY or "").strip()
    base_url = (settings.OPENAI_BASE_URL or "").rstrip("/")
    if not has_valid_openai_key(key):
        status = {"status": "warn", "label": "LLM", "message": "키 미설정"}
    elif not base_url and not key.startswith("sk-"):
        status = {"status": "warn", "label": "LLM", "message": "서버 주소 필요"}
    else:
        url = f"{base_url or 'https://api.openai.com/v1'}/chat/completions"
        try:
            async with httpx.AsyncClient(timeout=6) as client:
                response = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {key}"},
                    json={
                        "model": settings.OPENAI_QA_MODEL,
                        "messages": [{"role": "user", "content": "ping"}],
                        "max_tokens": 1,
                    },
                )
            if response.status_code == 200:
                status = {"status": "ok", "label": "LLM", "message": "응답 정상"}
            elif response.status_code in (401, 403):
                status = {"status": "bad", "label": "LLM", "message": "인증 실패"}
            elif response.status_code == 429:
                status = {"status": "warn", "label": "LLM", "message": "사용량 제한"}
            elif response.status_code >= 500:
                status = {
                    "status": "bad",
                    "label": "LLM",
                    "message": f"제공 서버 오류({response.status_code})",
                }
            else:
                status = {
                    "status": "bad",
                    "label": "LLM",
                    "message": f"응답 오류 {response.status_code}",
                }
        except Exception:
            status = {"status": "bad", "label": "LLM", "message": "연결 실패"}

    _llm_cache = (now, status)
    return status
