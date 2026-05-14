from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sqlalchemy import text

from app.db import get_engine
from app.ingestion.ingestion_utils import IngestionLog, bootstrap_schema, insert_ingestion_log, now_utc_iso, retry, upsert_source_metadata

FALLBACK = {
    "FPT": ("FPT Corporation", "HOSE", "Technology", "fallback_static_metadata"),
    "HPG": ("Hoa Phat Group", "HOSE", "Materials", "fallback_static_metadata"),
    "VCB": ("Vietcombank", "HOSE", "Financial Services", "fallback_static_metadata"),
    "VNM": ("Vinamilk", "HOSE", "Consumer Staples", "fallback_static_metadata"),
}


@dataclass
class CompanyRecord:
    ticker: str
    company_name: str
    exchange: str
    sector: str
    description: str
    source: str
    source_url: str
    fetched_at: str


def fetch_company_vnstock(ticker: str) -> CompanyRecord:
    from vnstock import Vnstock  # type: ignore

    stock = Vnstock().stock(symbol=ticker, source="VCI")
    ov = stock.company.overview()
    if not isinstance(ov, pd.DataFrame):
        ov = pd.DataFrame(ov)
    if ov.empty:
        raise ValueError("empty overview")
    rec = ov.iloc[0].to_dict()
    return CompanyRecord(
        ticker=ticker,
        company_name=str(rec.get("companyName") or rec.get("company_name") or FALLBACK[ticker][0]),
        exchange=str(rec.get("exchange") or rec.get("comGroupCode") or FALLBACK[ticker][1]),
        sector=str(rec.get("industryName") or rec.get("industry") or FALLBACK[ticker][2]),
        description=str(rec.get("companyProfile") or rec.get("description") or f"Profile for {ticker}")[:600],
        source="vnstock",
        source_url="https://github.com/thinh-vu/vnstock",
        fetched_at=now_utc_iso(),
    )


def fallback_company(ticker: str) -> CompanyRecord:
    name, exch, sect, src = FALLBACK[ticker]
    return CompanyRecord(
        ticker=ticker,
        company_name=name,
        exchange=exch,
        sector=sect,
        description=f"Fallback static metadata for {ticker}.",
        source=src,
        source_url="local_static_mapping",
        fetched_at=now_utc_iso(),
    )


def upsert_companies(rows: list[CompanyRecord]) -> int:
    if not rows:
        return 0
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO companies (ticker, company_name, exchange, sector, description, source, source_url, fetched_at)
                VALUES (:ticker, :company_name, :exchange, :sector, :description, :source, :source_url, :fetched_at)
                ON CONFLICT(ticker) DO UPDATE SET
                    company_name = excluded.company_name,
                    exchange = excluded.exchange,
                    sector = excluded.sector,
                    description = excluded.description,
                    source = excluded.source,
                    source_url = excluded.source_url,
                    fetched_at = excluded.fetched_at
                """
            ),
            [r.__dict__ for r in rows],
        )
    return len(rows)


def run_company_ingestion(tickers: list[str]) -> list[IngestionLog]:
    bootstrap_schema()
    upsert_source_metadata(
        source="vnstock",
        source_type="company_profile",
        url="https://github.com/thinh-vu/vnstock",
        limitations="Some profile fields can be null/missing per ticker.",
        legal_caveats="Use for analysis/demo purposes; verify terms for redistribution.",
        fallback_behavior="Fallback to local static metadata if API fails.",
    )
    logs: list[IngestionLog] = []
    rows: list[CompanyRecord] = []
    for ticker in tickers:
        try:
            row = retry(lambda: fetch_company_vnstock(ticker), attempts=2)
            rows.append(row)
            log = IngestionLog("company", ticker, row.source, "ok", 1, 1, "")
        except Exception as exc:  # noqa: BLE001
            row = fallback_company(ticker)
            rows.append(row)
            log = IngestionLog("company", ticker, row.source, "fallback", 1, 1, str(exc))
        insert_ingestion_log(log)
        logs.append(log)
    upsert_companies(rows)
    return logs


if __name__ == "__main__":
    res = run_company_ingestion(["FPT", "HPG", "VCB", "VNM"])
    for r in res:
        print(f"[{r.status}] company:{r.ticker} source={r.source} msg={r.message}")
