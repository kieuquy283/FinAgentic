from __future__ import annotations

import argparse
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text

from app.db import ensure_runtime_tables, get_engine
from app.ingestion.freshness import is_price_stale, is_profile_stale
from app.tools.vnstock_tools import get_company_profile, get_financial_ratios, get_price_history


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _log(source: str, job_type: str, ticker: str, status: str, message: str, started_at: str) -> None:
    with get_engine().begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO ingestion_logs (source, job_type, ticker, status, message, started_at, finished_at, run_at, ingestion_type, records_raw, records_upserted)
                VALUES (:source, :job_type, :ticker, :status, :message, :started_at, :finished_at, :run_at, :ingestion_type, :records_raw, :records_upserted)
                """
            ),
            {
                "source": source,
                "job_type": job_type,
                "ticker": ticker,
                "status": status,
                "message": message,
                "started_at": started_at,
                "finished_at": _now_iso(),
                "run_at": _now_iso(),
                "ingestion_type": job_type,
                "records_raw": 0,
                "records_upserted": 0,
            },
        )


def upsert_prices(rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0
    with get_engine().begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO prices (ticker, date, open, high, low, close, volume, source, fetched_at, data_date)
                VALUES (:ticker, :date, :open, :high, :low, :close, :volume, :source, :fetched_at, :data_date)
                ON CONFLICT(ticker, date) DO UPDATE SET
                    open = excluded.open,
                    high = excluded.high,
                    low = excluded.low,
                    close = excluded.close,
                    volume = excluded.volume,
                    source = excluded.source,
                    fetched_at = excluded.fetched_at,
                    data_date = excluded.data_date
                """
            ),
            [{**r, "data_date": r["date"]} for r in rows],
        )
    return len(rows)


def upsert_companies(rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0
    with get_engine().begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO companies (ticker, company_name, name, exchange, sector, industry, description, source, fetched_at)
                VALUES (:ticker, :company_name, :name, :exchange, :sector, :industry, :description, :source, :fetched_at)
                ON CONFLICT(ticker) DO UPDATE SET
                    company_name = excluded.company_name,
                    name = excluded.name,
                    exchange = excluded.exchange,
                    sector = excluded.sector,
                    industry = excluded.industry,
                    description = excluded.description,
                    source = excluded.source,
                    fetched_at = excluded.fetched_at
                """
            ),
            [
                {
                    "ticker": r["ticker"],
                    "company_name": r.get("name") or r["ticker"],
                    "name": r.get("name"),
                    "exchange": r.get("exchange") or "UNKNOWN",
                    "sector": r.get("sector") or "UNKNOWN",
                    "industry": r.get("industry") or "UNKNOWN",
                    "description": f"Profile for {r['ticker']}",
                    "source": r["source"],
                    "fetched_at": r["fetched_at"],
                }
                for r in rows
            ],
        )
    return len(rows)


def upsert_financial_ratios(rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0
    with get_engine().begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO financial_ratios (ticker, metric, value, period, source, fetched_at, data_date)
                VALUES (:ticker, :metric, :value, :period, :source, :fetched_at, NULL)
                ON CONFLICT(ticker, metric, period) DO UPDATE SET
                    value = excluded.value,
                    source = excluded.source,
                    fetched_at = excluded.fetched_at
                """
            ),
            rows,
        )
    return len(rows)


def ingest_ticker_data(ticker: str, do_prices: bool = False, do_profile: bool = False, do_all: bool = False) -> dict[str, Any]:
    ensure_runtime_tables()
    started_at = _now_iso()
    result = {"ticker": ticker, "prices": 0, "profile": 0, "ratios": 0, "warnings": []}

    if do_all or do_prices:
        try:
            prices = get_price_history(ticker, "2025-01-01", datetime.now(timezone.utc).date().isoformat())
            result["warnings"].extend(prices.warnings)
            result["prices"] = upsert_prices(prices.data)
            _log("vnstock", "prices", ticker, "ok", f"upserted={result['prices']}", started_at)
        except Exception as exc:  # noqa: BLE001
            _log("vnstock", "prices", ticker, "error", str(exc), started_at)
            result["warnings"].append(f"prices_error:{exc}")

    if do_all or do_profile:
        try:
            profile = get_company_profile(ticker)
            ratios = get_financial_ratios(ticker) if do_all else None
            result["warnings"].extend(profile.warnings)
            result["profile"] = upsert_companies(profile.data)
            _log("vnstock", "profile", ticker, "ok", f"upserted={result['profile']}", started_at)
            if ratios is not None:
                result["warnings"].extend(ratios.warnings)
                result["ratios"] = upsert_financial_ratios(ratios.data)
                _log("vnstock", "ratios", ticker, "ok", f"upserted={result['ratios']}", started_at)
        except Exception as exc:  # noqa: BLE001
            _log("vnstock", "profile", ticker, "error", str(exc), started_at)
            result["warnings"].append(f"profile_error:{exc}")
    return result


def refresh_if_needed(ticker: str) -> dict[str, Any]:
    ensure_runtime_tables()
    with get_engine().connect() as conn:
        latest_price = conn.execute(
            text("SELECT MAX(date) AS d FROM prices WHERE ticker=:ticker"),
            {"ticker": ticker},
        ).mappings().first()
        company = conn.execute(
            text("SELECT fetched_at FROM companies WHERE ticker=:ticker"),
            {"ticker": ticker},
        ).mappings().first()

    need_prices = is_price_stale(latest_price["d"] if latest_price else None)
    need_profile = is_profile_stale(company["fetched_at"] if company else None)
    refreshed = False
    warnings: list[str] = []
    if need_prices or need_profile:
        refreshed = True
        resp = ingest_ticker_data(ticker, do_prices=need_prices, do_profile=need_profile, do_all=False)
        warnings.extend(resp["warnings"])
    return {"refreshed": refreshed, "need_prices": need_prices, "need_profile": need_profile, "warnings": warnings}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tickers", nargs="+", required=True)
    parser.add_argument("--prices", action="store_true")
    parser.add_argument("--profile", action="store_true")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    for t in args.tickers:
        try:
            out = ingest_ticker_data(t.upper(), do_prices=args.prices, do_profile=args.profile, do_all=args.all)
            print(f"[ok] {t} prices={out['prices']} profile={out['profile']} ratios={out['ratios']} warnings={len(out['warnings'])}")
        except Exception as exc:  # noqa: BLE001
            print(f"[error] {t} {exc}")


if __name__ == "__main__":
    main()

