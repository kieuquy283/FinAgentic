from __future__ import annotations

from app.schemas import ChatResponse

_CACHE: dict[str, ChatResponse] = {}


def normalize_query(query: str) -> str:
    return " ".join(query.strip().lower().split())


def get_cache(key: str):
    return _CACHE.get(key)


def set_cache(key: str, value: ChatResponse) -> None:
    _CACHE[key] = value
