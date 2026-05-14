from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import pandas as pd
from sqlalchemy import text

from app.db import get_engine
from app.ingestion.ingestion_utils import (
    IngestionLog,
    bootstrap_schema,
    insert_ingestion_log,
    now_utc_iso,
    retry,
    upsert_raw_item,
    upsert_source_metadata,
)


@dataclass
class PriceRecord:
    ticker: str
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    source: str
    source_url: str
    fetched_at: str


def normalize_ohlcv(df: pd.DataFrame, ticker: str, source: str, source_url: str) -> list[PriceRecord]:
    if df is None or df.empty:
        return []
    cols = {str(c).lower(): c for c in df.columns}

    def pick(*names: str) -> str:
        for n in names:
            if n in cols:
                return cols[n]
        raise KeyError(f"missing column {names}")

    date_col = pick("date", "time", "tradingdate")
    open_col = pick("open")
    high_col = pick("high")
    low_col = pick("low")
    close_col = pick("close")
    vol_col = pick("volume", "vol")
    fetched_at = now_utc_iso()
    out: list[PriceRecord] = []
    for _, r in df.iterrows():
        try:
            d = pd.to_datetime(r[date_col]).date().isoformat()
            o = float(r[open_col])
            h = float(r[high_col])
            l = float(r[low_col])
            c = float(r[close_col])
            v = int(float(r[vol_col]))
        except Exception:
            continue
        if v < 0:
            continue
        out.append(PriceRecord(ticker, d, o, h, l, c, v, source, source_url, fetched_at))
    return out


def fetch_ohlcv_vnstock(ticker: str, start: str, end: str) -> pd.DataFrame:
    from vnstock import Vnstock  # type: ignore

    stock = Vnstock().stock(symbol=ticker, source="VCI")
    hist = stock.quote.history(start=start, end=end, interval="1D")
    if isinstance(hist, pd.DataFrame):
        return hist
    return pd.DataFrame(hist)


def upsert_prices(rows: list[PriceRecord]) -> int:
    if not rows:
        return 0
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO prices (ticker, date, open, high, low, close, volume, source, source_url, fetched_at, data_date)
                VALUES (:ticker, :date, :open, :high, :low, :close, :volume, :source, :source_url, :fetched_at, :data_date)
                ON CONFLICT(ticker, date) DO UPDATE SET
                    open = excluded.open,
                    high = excluded.high,
                    low = excluded.low,
                    close = excluded.close,
                    volume = excluded.volume,
                    source = excluded.source,
                    source_url = excluded.source_url,
                    fetched_at = excluded.fetched_at,
                    data_date = excluded.data_date
                """
            ),
            [
                {
                    "ticker": r.ticker,
                    "date": r.date,
                    "open": r.open,
                    "high": r.high,
                    "low": r.low,
                    "close": r.close,
                    "volume": r.volume,
                    "source": r.source,
                    "source_url": r.source_url,
                    "fetched_at": r.fetched_at,
                    "data_date": r.date,
                }
                for r in rows
            ],
        )
    return len(rows)


def run_market_ingestion(tickers: list[str], lookback_days: int = 365) -> list[IngestionLog]:
    bootstrap_schema()
    source = "vnstock"
    source_url = "https://github.com/thinh-vu/vnstock"
    upsert_source_metadata(
        source=source,
        source_type="market_prices",
        url=source_url,
        limitations="API behavior may change; data gaps can exist by ticker/session.",
        legal_caveats="Use for analysis/demo, verify source terms before redistribution.",
        fallback_behavior="If fetch fails for a ticker, log error and continue other tickers.",
    )
    start = (date.today() - timedelta(days=lookback_days)).isoformat()
    end = date.today().isoformat()
    logs: list[IngestionLog] = []
    for ticker in tickers:
        try:
            df = retry(lambda: fetch_ohlcv_vnstock(ticker, start, end), attempts=3)
            rows = normalize_ohlcv(df, ticker, source, source_url)
            for r in rows[:20]:
                upsert_raw_item(
                    item_id=f"raw_price:{ticker}:{r.date}",
                    ingestion_type="market",
                    ticker=ticker,
                    source=source,
                    source_url=source_url,
                    data_date=r.date,
                    payload={
                        "ticker": r.ticker,
                        "date": r.date,
                        "open": r.open,
                        "high": r.high,
                        "low": r.low,
                        "close": r.close,
                        "volume": r.volume,
                    },
                )
            up = upsert_prices(rows)
            log = IngestionLog("market", ticker, source, "ok" if up > 0 else "empty", len(rows), up, f"{start}->{end}")
        except Exception as exc:  # noqa: BLE001
            log = IngestionLog("market", ticker, source, "error", 0, 0, str(exc))
        insert_ingestion_log(log)
        logs.append(log)
    return logs


if __name__ == "__main__":
    results = run_market_ingestion(["FPT", "HPG", "VCB", "VNM"])
    for r in results:
        print(f"[{r.status}] market:{r.ticker} raw={r.records_raw} upserted={r.records_upserted} msg={r.message}")
