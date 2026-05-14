from __future__ import annotations

from sqlalchemy import text

from app.db import get_engine


class MarketDataService:
    def get_prices(self, ticker: str, limit: int = 90):
        if not ticker:
            return []
        engine = get_engine()
        with engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT date, open, high, low, close, volume, source, fetched_at
                    FROM prices
                    WHERE ticker = :ticker
                    ORDER BY date DESC
                    LIMIT :limit
                    """
                ),
                {"ticker": ticker, "limit": limit},
            ).mappings().all()
        return list(reversed(rows))

    def summarize_3m(self, ticker: str):
        rows = self.get_prices(ticker, 90)
        if not rows:
            return None
        start_close = float(rows[0]["close"])
        latest_close = float(rows[-1]["close"])
        ret = round((latest_close - start_close) / start_close * 100, 2)
        vol = [int(r["volume"]) for r in rows[-20:]]
        avg_vol = round(sum(vol) / len(vol), 2) if vol else 0.0
        return {
            "ticker": ticker,
            "latest_close": latest_close,
            "start_close": start_close,
            "return_3m_pct": ret,
            "avg_volume_20d": avg_vol,
            "date_from": rows[0]["date"],
            "date_to": rows[-1]["date"],
        }
