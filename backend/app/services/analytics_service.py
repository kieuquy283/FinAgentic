from __future__ import annotations

import numpy as np


class AnalyticsService:
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
