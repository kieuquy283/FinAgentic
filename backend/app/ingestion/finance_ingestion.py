from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sqlalchemy import text

from app.db import get_engine
from app.ingestion.ingestion_utils import IngestionLog, bootstrap_schema, insert_ingestion_log, now_utc_iso, retry, upsert_source_metadata


@dataclass
class RatioRecord:
    ticker: str
    metric: str
    value: float | None
    period: str
    source: str
    source_url: str
    fetched_at: str
    data_date: str | None


def _extract_ratios_from_df(df: pd.DataFrame, ticker: str) -> list[RatioRecord]:
    rows: list[RatioRecord] = []
    if df is None or df.empty:
        return rows
    cols = {str(c).lower(): c for c in df.columns}
    metric_col = cols.get("metric") or cols.get("ratio") or list(df.columns)[0]
    value_col = cols.get("value") or (list(df.columns)[1] if len(df.columns) > 1 else list(df.columns)[0])
    period_col = cols.get("period") or cols.get("year") or metric_col
    for _, r in df.iterrows():
        metric = str(r.get(metric_col, "")).strip()
        if not metric:
            continue
        try:
            value = float(r.get(value_col)) if r.get(value_col) is not None else None
        except Exception:
            value = None
        period = str(r.get(period_col) or "unknown")
        rows.append(RatioRecord(ticker, metric, value, period, "vnstock", "https://github.com/thinh-vu/vnstock", now_utc_iso(), None))
    return rows


def fetch_finance_ratios_vnstock(ticker: str) -> list[RatioRecord]:
    from vnstock import Vnstock  # type: ignore

    stock = Vnstock().stock(symbol=ticker, source="VCI")
    # API shape can change; this is intentionally tolerant.
    ratios = stock.finance.ratio(period="year", lang="vi", dropna=True)
    if not isinstance(ratios, pd.DataFrame):
        ratios = pd.DataFrame(ratios)
    return _extract_ratios_from_df(ratios, ticker)


def upsert_financial_ratios(rows: list[RatioRecord]) -> int:
    if not rows:
        return 0
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO financial_ratios (ticker, metric, value, period, source, source_url, fetched_at, data_date)
                VALUES (:ticker, :metric, :value, :period, :source, :source_url, :fetched_at, :data_date)
                ON CONFLICT(ticker, metric, period) DO UPDATE SET
                    value = excluded.value,
                    source = excluded.source,
                    source_url = excluded.source_url,
                    fetched_at = excluded.fetched_at,
                    data_date = excluded.data_date
                """
            ),
            [r.__dict__ for r in rows],
        )
    return len(rows)


def run_finance_ingestion(tickers: list[str]) -> list[IngestionLog]:
    bootstrap_schema()
    upsert_source_metadata(
        source="vnstock_finance",
        source_type="financial_ratios",
        url="https://github.com/thinh-vu/vnstock",
        limitations="Ratio endpoints can be unavailable or schema-variant by ticker.",
        legal_caveats="Use for analysis/demo only; validate terms and metric definitions.",
        fallback_behavior="Log skipped when unavailable; continue ingestion job.",
    )
    logs: list[IngestionLog] = []
    for ticker in tickers:
        try:
            rows = retry(lambda: fetch_finance_ratios_vnstock(ticker), attempts=2)
            up = upsert_financial_ratios(rows)
            status = "ok" if up > 0 else "skipped"
            log = IngestionLog("finance", ticker, "vnstock_finance", status, len(rows), up, "")
        except Exception as exc:  # noqa: BLE001
            log = IngestionLog("finance", ticker, "vnstock_finance", "skipped", 0, 0, str(exc))
        insert_ingestion_log(log)
        logs.append(log)
    return logs


if __name__ == "__main__":
    rs = run_finance_ingestion(["FPT", "HPG", "VCB", "VNM"])
    for r in rs:
        print(f"[{r.status}] finance:{r.ticker} msg={r.message}")
