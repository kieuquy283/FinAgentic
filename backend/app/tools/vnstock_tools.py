from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import re
from typing import Any

import pandas as pd

from app.tools.schemas import ToolResponse

SOURCE = "vnstock"
SOURCE_URL = "https://github.com/thinh-vu/vnstock"
TICKER_RE = re.compile(r"^[A-Z]{3,5}$")


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _validate_ticker(ticker: str) -> str:
    t = (ticker or "").strip().upper()
    if not TICKER_RE.match(t):
        raise ValueError(f"invalid ticker: {ticker}")
    return t


def _to_frame(obj: Any) -> pd.DataFrame:
    if isinstance(obj, pd.DataFrame):
        return obj
    return pd.DataFrame(obj)


def _normalize_prices(df: pd.DataFrame, ticker: str, fetched_at: str) -> list[dict[str, Any]]:
    if df.empty:
        return []
    cols = {str(c).lower(): c for c in df.columns}

    def pick(*names: str) -> str:
        for n in names:
            if n in cols:
                return cols[n]
        raise KeyError(f"missing column {names}")

    out: list[dict[str, Any]] = []
    for _, r in df.iterrows():
        try:
            out.append(
                {
                    "ticker": ticker,
                    "date": pd.to_datetime(r[pick("date", "time", "tradingdate")]).date().isoformat(),
                    "open": float(r[pick("open")]),
                    "high": float(r[pick("high")]),
                    "low": float(r[pick("low")]),
                    "close": float(r[pick("close")]),
                    "volume": int(float(r[pick("volume", "vol")])),
                    "source": SOURCE,
                    "fetched_at": fetched_at,
                }
            )
        except Exception:
            continue
    return out


def get_price_history(ticker: str, start: str, end: str, interval: str = "1D") -> ToolResponse:
    t = _validate_ticker(ticker)
    fetched_at = _now_iso()
    warnings: list[str] = []
    try:
        from vnstock import Vnstock  # type: ignore

        stock = Vnstock().stock(symbol=t, source="VCI")
        df = _to_frame(stock.quote.history(start=start, end=end, interval=interval))
        data = _normalize_prices(df, t, fetched_at)
        if not data:
            warnings.append("empty_or_unparseable_price_response")
        return ToolResponse(fetched_at=fetched_at, data_type="price_history", data=data, warnings=warnings)
    except Exception as exc:  # noqa: BLE001
        return ToolResponse(fetched_at=fetched_at, data_type="price_history", data=[], warnings=[f"fetch_failed:{exc}"])


def get_company_profile(ticker: str) -> ToolResponse:
    t = _validate_ticker(ticker)
    fetched_at = _now_iso()
    try:
        from vnstock import Vnstock  # type: ignore

        stock = Vnstock().stock(symbol=t, source="VCI")
        df = _to_frame(stock.company.overview())
        if df.empty:
            return ToolResponse(fetched_at=fetched_at, data_type="company_profile", data=[], warnings=["empty_profile"])
        rec = df.iloc[0].to_dict()
        row = {
            "ticker": t,
            "name": str(rec.get("companyName") or rec.get("company_name") or t),
            "exchange": str(rec.get("exchange") or rec.get("comGroupCode") or "UNKNOWN"),
            "sector": str(rec.get("industryName") or rec.get("sector") or "UNKNOWN"),
            "industry": str(rec.get("industry") or rec.get("industryName") or "UNKNOWN"),
            "source": SOURCE,
            "fetched_at": fetched_at,
        }
        return ToolResponse(fetched_at=fetched_at, data_type="company_profile", data=[row], warnings=[])
    except Exception as exc:  # noqa: BLE001
        return ToolResponse(fetched_at=fetched_at, data_type="company_profile", data=[], warnings=[f"fetch_failed:{exc}"])


def get_financial_ratios(ticker: str) -> ToolResponse:
    t = _validate_ticker(ticker)
    fetched_at = _now_iso()
    warnings: list[str] = []
    try:
        from vnstock import Vnstock  # type: ignore

        stock = Vnstock().stock(symbol=t, source="VCI")
        df = _to_frame(stock.finance.ratio(period="year", lang="vi", dropna=True))
        if df.empty:
            return ToolResponse(fetched_at=fetched_at, data_type="financial_ratios", data=[], warnings=["empty_ratios"])
        cols = {str(c).lower(): c for c in df.columns}
        metric_col = cols.get("metric") or cols.get("ratio") or list(df.columns)[0]
        value_col = cols.get("value") or (list(df.columns)[1] if len(df.columns) > 1 else metric_col)
        period_col = cols.get("period") or cols.get("year") or metric_col
        data = []
        for _, r in df.iterrows():
            m = str(r.get(metric_col, "")).strip()
            if not m:
                continue
            try:
                value = float(r.get(value_col)) if r.get(value_col) is not None else None
            except Exception:
                value = None
                warnings.append(f"non_numeric_value:{m}")
            data.append(
                {
                    "ticker": t,
                    "metric": m,
                    "value": value,
                    "period": str(r.get(period_col) or "unknown"),
                    "source": SOURCE,
                    "fetched_at": fetched_at,
                }
            )
        return ToolResponse(fetched_at=fetched_at, data_type="financial_ratios", data=data, warnings=warnings)
    except Exception as exc:  # noqa: BLE001
        return ToolResponse(fetched_at=fetched_at, data_type="financial_ratios", data=[], warnings=[f"fetch_failed:{exc}"])


def refresh_ticker_data(ticker: str, start: str | None = None, end: str | None = None) -> dict[str, Any]:
    t = _validate_ticker(ticker)
    end_date = end or date.today().isoformat()
    start_date = start or (date.today() - timedelta(days=365)).isoformat()
    prices = get_price_history(t, start_date, end_date, interval="1D")
    profile = get_company_profile(t)
    ratios = get_financial_ratios(t)
    return {
        "source": SOURCE,
        "source_url": SOURCE_URL,
        "fetched_at": _now_iso(),
        "ticker": t,
        "start": start_date,
        "end": end_date,
        "payloads": [prices.model_dump(), profile.model_dump(), ratios.model_dump()],
    }

