"""Korean terminology lookup integration."""

from __future__ import annotations

import json
import re
import time
import xml.etree.ElementTree as ET
from html import unescape
from typing import Any

import httpx

from app.core.config import settings


_status_cache: tuple[float, dict[str, str]] | None = None


def _clean_text(value: Any) -> str:
    text = "" if value is None else str(value)
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _raise_api_error(code: Any, message: Any) -> None:
    code_text = _clean_text(code)
    message_text = _clean_text(message)
    if code_text == "020" or "Unregistered" in message_text:
        raise ValueError("온용어 API 키가 등록되지 않았습니다. 사용 신청 상태를 확인해 주세요.")
    if code_text == "021":
        raise ValueError("온용어 API 키를 사용할 수 없습니다.")
    if code_text == "022":
        raise ValueError("온용어 API 일일 사용량을 초과했습니다.")
    raise ValueError(message_text or f"온용어 API 응답 오류 {code_text}".strip())


def _items_from_json(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, str):
        payload = json.loads(payload)
    if not isinstance(payload, dict):
        return []

    error = payload.get("error") or payload.get("Error")
    if isinstance(error, dict):
        _raise_api_error(error.get("error_code") or error.get("code"), error.get("message"))

    channel = payload.get("channel", payload)
    if not isinstance(channel, dict):
        return []

    return_object = channel.get("return_object")
    if isinstance(return_object, str):
        raise ValueError(_clean_text(return_object))

    items: list[dict[str, Any]] = []
    for group in _listify(return_object):
        if not isinstance(group, dict):
            continue
        return_code = str(group.get("returnCode", "1"))
        if return_code != "1":
            _raise_api_error(return_code, group.get("message"))
        items.extend(item for item in _listify(group.get("resultlist")) if isinstance(item, dict))

    fallback_items = channel.get("item") or channel.get("items") or payload.get("item") or []
    items.extend(item for item in _listify(fallback_items) if isinstance(item, dict))
    return items


def _items_from_xml(text: str) -> list[dict[str, Any]]:
    root = ET.fromstring(text)
    error = root if root.tag == "error" else root.find(".//error")
    if error is not None:
        _raise_api_error(error.findtext("error_code"), error.findtext("message"))

    items: list[dict[str, Any]] = []
    for item in root.findall(".//item"):
        parsed: dict[str, Any] = {}
        for child in list(item):
            parsed[child.tag] = _clean_text(child.text)
        items.append(parsed)
    return items


def _serialize(item: dict[str, Any]) -> dict[str, str]:
    source_parts = [
        _clean_text(item.get("source")),
        _clean_text(item.get("glossary")),
    ]
    category_parts = [
        _clean_text(item.get("category_main")),
        _clean_text(item.get("category_sub")),
    ]
    return {
        "word": _clean_text(item.get("word")),
        "definition": _clean_text(item.get("definition")),
        "pos": " / ".join(part for part in category_parts if part),
        "link": "",
        "source": " · ".join(part for part in source_parts if part) or "온용어",
    }


async def search_dictionary(q: str, limit: int = 5) -> list[dict[str, str]]:
    key = (settings.DICTIONARY_API_KEY or "").strip()
    if not key:
        raise ValueError("온용어 API 키가 설정되지 않았습니다.")

    params = {
        "key": key,
        "apiSearchWord": q,
        "req_type": "json",
        "start": "1",
        "num": str(max(1, min(limit, 100))),
        "sort": "wt",
    }
    async with httpx.AsyncClient(timeout=8) as client:
        response = await client.get(settings.DICTIONARY_API_URL, params=params)

    text = response.text.strip()
    if response.status_code >= 400:
        raise ValueError(f"온용어 API 응답 오류 {response.status_code}")
    if not text:
        return []

    try:
        items = _items_from_json(response.json())
    except json.JSONDecodeError:
        items = _items_from_xml(text)

    return [
        result
        for result in (_serialize(item) for item in items)
        if result["word"] or result["definition"]
    ][:limit]


async def get_dictionary_status() -> dict[str, str]:
    global _status_cache

    now = time.monotonic()
    if _status_cache and now - _status_cache[0] < 300:
        return _status_cache[1]

    key = (settings.DICTIONARY_API_KEY or "").strip()
    if not key:
        status = {"status": "warn", "label": "온용어", "message": "키 미설정"}
    else:
        try:
            results = await search_dictionary("물고기", limit=1)
            status = (
                {"status": "ok", "label": "온용어", "message": "정상"}
                if results
                else {"status": "warn", "label": "온용어", "message": "결과 없음"}
            )
        except ValueError:
            status = {"status": "bad", "label": "온용어", "message": "키 확인 필요"}
        except Exception:
            status = {"status": "bad", "label": "온용어", "message": "연결 실패"}

    _status_cache = (now, status)
    return status
