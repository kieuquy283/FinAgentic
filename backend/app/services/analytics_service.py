from __future__ import annotations

import numpy as np
from sqlalchemy import text

from app.db import get_engine


class AnalyticsService:
    def get_close_prices(self, ticker: str, limit: int = 120) -> list[float]:
        if not ticker:
            return []
        ticker = ticker.strip().upper()
        with get_engine().connect() as conn:
            rows = conn.execute(
                text("SELECT close FROM prices WHERE ticker=:ticker ORDER BY date DESC LIMIT :limit"),
                {"ticker": ticker, "limit": limit},
            ).mappings().all()
        return [float(r["close"]) for r in reversed(rows)]

    def calculate_sma(self, prices: list[float], window: int = 20) -> float:
        if len(prices) < window:
            raise ValueError("insufficient data for SMA")
        return round(float(np.mean(prices[-window:])), 2)

    def calculate_rsi(self, prices: list[float], window: int = 14) -> float:
        if len(prices) < window + 1:
            raise ValueError("insufficient data for RSI")
        deltas = np.diff(np.array(prices, dtype=float))
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain = np.mean(gains[-window:])
        avg_loss = np.mean(losses[-window:])
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return round(float(100 - 100 / (1 + rs)), 2)

    def calculate_return_pct(self, prices: list[float]) -> float:
        if len(prices) < 2:
            raise ValueError("insufficient data for return")
        return round((prices[-1] - prices[0]) / prices[0] * 100, 2)

    def get_latest_close_prices(self, ticker: str, limit: int) -> tuple[list[float], str | None]:
        if not ticker or limit <= 0:
            return [], None
        ticker = ticker.strip().upper()
        with get_engine().connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT date, close
                    FROM prices
                    WHERE ticker=:ticker
                    ORDER BY date DESC
                    LIMIT :limit
                    """
                ),
                {"ticker": ticker, "limit": limit},
            ).mappings().all()
        if not rows:
            return [], None
        latest_date = str(rows[0]["date"])
        prices = [float(r["close"]) for r in reversed(rows)]
        return prices, latest_date

    def get_latest_price_date(self, ticker: str) -> str | None:
        if not ticker:
            return None
        ticker = ticker.strip().upper()
        with get_engine().connect() as conn:
            row = conn.execute(
                text("SELECT MAX(date) AS latest_date FROM prices WHERE ticker=:ticker"),
                {"ticker": ticker},
            ).mappings().first()
        if not row or not row.get("latest_date"):
            return None
        return str(row["latest_date"])
