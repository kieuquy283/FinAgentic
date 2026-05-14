from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import text

from app.db import ensure_runtime_tables, get_engine
from app.ingestion.vnstock_ingestion import ingest_ticker_data

DEFAULT_TICKERS = ["FPT", "HPG", "VCB", "VNM"]
_SCHEDULER: Any | None = None
_LAST_JOB_SUMMARY: dict | None = None

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger

    APSCHEDULER_AVAILABLE = True
except Exception:  # noqa: BLE001
    APSCHEDULER_AVAILABLE = False


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _as_bool(v: str | None, default: bool = True) -> bool:
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "on"}


def get_refresh_tickers() -> list[str]:
    raw = os.getenv("REFRESH_TICKERS", "FPT,HPG,VCB,VNM")
    vals = [x.strip().upper() for x in raw.split(",") if x.strip()]
    return vals or DEFAULT_TICKERS


def is_scheduler_enabled() -> bool:
    return _as_bool(os.getenv("DAILY_REFRESH_ENABLED", "true"), default=True)


def _scheduler_timezone() -> str:
    return os.getenv("APP_TIMEZONE", "Asia/Ho_Chi_Minh").strip() or "Asia/Ho_Chi_Minh"


def run_refresh_job(tickers: list[str] | None = None) -> dict:
    ensure_runtime_tables()
    selected = [t.strip().upper() for t in (tickers or get_refresh_tickers()) if t and t.strip()]
    started_at = _now_iso()
    results = []
    ok = 0
    failed = 0
    for t in selected:
        try:
            out = ingest_ticker_data(ticker=t, do_all=True)
            results.append({"ticker": t, "status": "ok", **out})
            ok += 1
        except Exception as exc:  # noqa: BLE001
            results.append({"ticker": t, "status": "error", "error": str(exc)})
            failed += 1
    finished_at = _now_iso()
    summary = {
        "job": "daily_refresh",
        "started_at": started_at,
        "finished_at": finished_at,
        "tickers": selected,
        "ok": ok,
        "failed": failed,
        "results": results,
    }
    global _LAST_JOB_SUMMARY
    _LAST_JOB_SUMMARY = summary
    return summary


def _scheduled_job_wrapper() -> None:
    try:
        run_refresh_job()
    except Exception:  # noqa: BLE001
        # Never crash scheduler thread
        return


def start_daily_refresh_scheduler() -> bool:
    global _SCHEDULER
    if not APSCHEDULER_AVAILABLE:
        return False
    if not is_scheduler_enabled():
        return False
    if _SCHEDULER is not None and _SCHEDULER.running:
        return True
    tz_name = _scheduler_timezone()
    scheduler = BackgroundScheduler(timezone=ZoneInfo(tz_name))
    hour = int(os.getenv("DAILY_REFRESH_HOUR", "18"))
    minute = int(os.getenv("DAILY_REFRESH_MINUTE", "30"))
    scheduler.add_job(
        _scheduled_job_wrapper,
        trigger=CronTrigger(hour=hour, minute=minute, timezone=ZoneInfo(tz_name)),
        id="daily-vnstock-refresh",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )
    scheduler.start()
    _SCHEDULER = scheduler
    return True


def stop_daily_refresh_scheduler() -> None:
    global _SCHEDULER
    if _SCHEDULER is not None:
        _SCHEDULER.shutdown(wait=False)
        _SCHEDULER = None


def refresh_status() -> dict:
    ensure_runtime_tables()
    with get_engine().connect() as conn:
        last_ok = conn.execute(
            text(
                """
                SELECT finished_at, ticker, message
                FROM ingestion_logs
                WHERE source='vnstock' AND status='ok'
                ORDER BY COALESCE(finished_at, run_at) DESC
                LIMIT 1
                """
            )
        ).mappings().first()
        last_fail = conn.execute(
            text(
                """
                SELECT finished_at, ticker, message
                FROM ingestion_logs
                WHERE source='vnstock' AND status='error'
                ORDER BY COALESCE(finished_at, run_at) DESC
                LIMIT 1
                """
            )
        ).mappings().first()
        latest_by_ticker_rows = conn.execute(
            text(
                """
                SELECT ticker, MAX(date) AS latest_date
                FROM prices
                GROUP BY ticker
                ORDER BY ticker
                """
            )
        ).mappings().all()
    latest_by_ticker = {str(r["ticker"]): str(r["latest_date"]) for r in latest_by_ticker_rows}
    return {
        "scheduler_enabled": is_scheduler_enabled(),
        "timezone": _scheduler_timezone(),
        "tickers": get_refresh_tickers(),
        "last_successful_refresh": dict(last_ok) if last_ok else None,
        "last_failed_refresh": dict(last_fail) if last_fail else None,
        "latest_data_date_by_ticker": latest_by_ticker,
        "last_job_summary": _LAST_JOB_SUMMARY,
    }
