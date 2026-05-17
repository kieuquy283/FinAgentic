from __future__ import annotations

import time
from dataclasses import dataclass

from app.schemas import ChatResponse

_CACHE: dict[str, ChatResponse] = {}
_GENERIC_CACHE: dict[str, "_CacheEntry"] = {}


@dataclass
class _CacheEntry:
    value: object
    expires_at: float | None = None


def normalize_query(query: str) -> str:
    return " ".join(query.strip().lower().split())


def get_cache(key: str):
    return _CACHE.get(key)


def set_cache(key: str, value: ChatResponse) -> None:
    _CACHE[key] = value


def get_cached_value(key: str):
    item = _GENERIC_CACHE.get(key)
    if item is None:
        return None
    if item.expires_at is not None and time.time() > item.expires_at:
        _GENERIC_CACHE.pop(key, None)
        return None
    return item.value


def set_cached_value(key: str, value: object, ttl_seconds: int | None = None) -> None:
    expires_at = None if ttl_seconds is None else (time.time() + ttl_seconds)
    _GENERIC_CACHE[key] = _CacheEntry(value=value, expires_at=expires_at)


def clear_all_caches() -> None:
    _CACHE.clear()
    _GENERIC_CACHE.clear()
