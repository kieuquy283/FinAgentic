from __future__ import annotations

from datetime import datetime, timedelta, timezone


def _parse_iso(dt: str | None) -> datetime | None:
    if not dt:
        return None
    try:
        return datetime.fromisoformat(dt.replace("Z", "+00:00"))
    except Exception:
        return None


def _market_days_ago(days: int) -> datetime:
    now = datetime.now(timezone.utc)
    cursor = now
    seen = 0
    while seen < days:
        cursor -= timedelta(days=1)
        if cursor.weekday() < 5:
            seen += 1
    return cursor


def is_price_stale(latest_date: str | None) -> bool:
    dt = _parse_iso(f"{latest_date}T00:00:00+00:00" if latest_date else None)
    if dt is None:
        return True
    return dt < _market_days_ago(3).replace(hour=0, minute=0, second=0, microsecond=0)


def is_profile_stale(fetched_at: str | None) -> bool:
    dt = _parse_iso(fetched_at)
    if dt is None:
        return True
    return dt < (datetime.now(timezone.utc) - timedelta(days=30))

