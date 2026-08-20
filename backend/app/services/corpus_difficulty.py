"""Load compact word-frequency statistics derived from NIKL corpora."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


CORPUS_STATS_PATH = Path(__file__).resolve().parents[1] / "data" / "nikl_term_frequency.json"


@lru_cache(maxsize=1)
def load_corpus_stats() -> dict[str, Any]:
    """Return generated statistics without requiring the licensed source corpora."""
    try:
        with CORPUS_STATS_PATH.open("r", encoding="utf-8") as file:
            payload = json.load(file)
    except (OSError, json.JSONDecodeError):
        return {"terms": {}, "metadata": {"available": False}}

    if not isinstance(payload, dict) or not isinstance(payload.get("terms"), dict):
        return {"terms": {}, "metadata": {"available": False}}
    return payload


def get_term_difficulty(term: str, fallback: int = 2) -> int:
    """Return 1(easy), 2(medium), or 3(hard), using the manual score as fallback."""
    item = load_corpus_stats().get("terms", {}).get(term)
    if not isinstance(item, dict):
        return fallback
    try:
        value = int(item.get("difficulty", fallback))
    except (TypeError, ValueError):
        return fallback
    return min(3, max(1, value))


def get_term_frequency(term: str) -> dict[str, Any] | None:
    item = load_corpus_stats().get("terms", {}).get(term)
    return item if isinstance(item, dict) else None

