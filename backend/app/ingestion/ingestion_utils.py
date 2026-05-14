from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha1
from typing import Any, Callable

from sqlalchemy import text

from app.db import ensure_runtime_tables, get_engine


TICKER_ALIASES: dict[str, list[str]] = {
    "FPT": ["fpt", "fpt corporation"],
    "HPG": ["hpg", "hoa phat"],
    "VCB": ["vcb", "vietcombank"],
    "VNM": ["vnm", "vinamilk"],
}


@dataclass
class IngestionLog:
    ingestion_type: str
    ticker: str | None
    source: str
    status: str
    records_raw: int
    records_upserted: int
    message: str = ""


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha_id(parts: list[str], size: int = 24) -> str:
    return sha1("|".join(parts).encode("utf-8")).hexdigest()[:size]


def retry(fn: Callable[[], Any], attempts: int = 3, base_sleep_seconds: float = 1.0) -> Any:
    err: Exception | None = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            err = exc
            if i < attempts - 1:
                time.sleep(base_sleep_seconds * (i + 1))
    assert err is not None
    raise err


def match_ticker(text_value: str) -> str | None:
    low = text_value.lower()
    for ticker, aliases in TICKER_ALIASES.items():
        if any(alias in low for alias in aliases):
            return ticker
    return None


def upsert_raw_item(
    item_id: str,
    ingestion_type: str,
    ticker: str | None,
    source: str,
    source_url: str | None,
    data_date: str | None,
    payload: dict[str, Any],
) -> None:
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO raw_ingestion_items (id, ingestion_type, ticker, source, source_url, fetched_at, data_date, payload)
                VALUES (:id, :ingestion_type, :ticker, :source, :source_url, :fetched_at, :data_date, :payload)
                ON CONFLICT(id) DO UPDATE SET
                    ingestion_type = excluded.ingestion_type,
                    ticker = excluded.ticker,
                    source = excluded.source,
                    source_url = excluded.source_url,
                    fetched_at = excluded.fetched_at,
                    data_date = excluded.data_date,
                    payload = excluded.payload
                """
            ),
            {
                "id": item_id,
                "ingestion_type": ingestion_type,
                "ticker": ticker,
                "source": source,
                "source_url": source_url,
                "fetched_at": now_utc_iso(),
                "data_date": data_date,
                "payload": json.dumps(payload, ensure_ascii=False),
            },
        )


def insert_ingestion_log(log: IngestionLog) -> None:
    engine = get_engine()
    with engine.begin() as conn:
        cols = {str(r["name"]) for r in conn.execute(text("PRAGMA table_info(ingestion_logs)")).mappings().all()}
        payload = {
            "run_at": now_utc_iso(),
            "ingestion_type": log.ingestion_type,
            "ticker": log.ticker,
            "source": log.source,
            "status": log.status,
            "records_raw": log.records_raw,
            "records_upserted": log.records_upserted,
            "message": log.message,
            "entity": f"{log.ingestion_type}:{log.ticker or 'all'}",
        }
        insert_cols = [c for c in ["run_at", "source", "entity", "status", "records_raw", "records_upserted", "message", "ingestion_type", "ticker"] if c in cols]
        if not insert_cols:
            return
        cols_sql = ", ".join(insert_cols)
        vals_sql = ", ".join(f":{c}" for c in insert_cols)
        conn.execute(text(f"INSERT INTO ingestion_logs ({cols_sql}) VALUES ({vals_sql})"), payload)


def upsert_source_metadata(
    source: str,
    source_type: str,
    url: str,
    limitations: str,
    legal_caveats: str,
    fallback_behavior: str,
) -> None:
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO source_metadata (source, source_type, url, limitations, legal_caveats, fallback_behavior, updated_at)
                VALUES (:source, :source_type, :url, :limitations, :legal_caveats, :fallback_behavior, :updated_at)
                ON CONFLICT(source) DO UPDATE SET
                    source_type = excluded.source_type,
                    url = excluded.url,
                    limitations = excluded.limitations,
                    legal_caveats = excluded.legal_caveats,
                    fallback_behavior = excluded.fallback_behavior,
                    updated_at = excluded.updated_at
                """
            ),
            {
                "source": source,
                "source_type": source_type,
                "url": url,
                "limitations": limitations,
                "legal_caveats": legal_caveats,
                "fallback_behavior": fallback_behavior,
                "updated_at": now_utc_iso(),
            },
        )


def bootstrap_schema() -> None:
    ensure_runtime_tables()
