from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api import deps
from app.models.user import User
from app.services.dictionary_service import search_dictionary

router = APIRouter()


@router.get("/search")
async def search(
    q: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    try:
        return {"query": q, "items": await search_dictionary(q, limit=limit)}
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="국어사전 조회에 실패했습니다.") from exc
