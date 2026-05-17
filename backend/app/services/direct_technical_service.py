from __future__ import annotations

from dataclasses import dataclass
import time

from app.cache import get_cached_value, set_cached_value
from app.schemas import EvidenceItem, RouterResult
from app.services.analytics_service import AnalyticsService
from app.services.market_data_service import MarketDataService
from app.services.router_scorer import IndicatorSpec, parse_indicator_spec


@dataclass
class DirectTechnicalResult:
    answer: str
    evidence: list[EvidenceItem]
    warnings: list[str]
    cache_hit: bool
    indicator: str
    window: int | None
    cache_ms: float = 0.0
    db_latest_date_ms: float = 0.0
    db_ms: float = 0.0
    analytics_ms: float = 0.0


class DirectTechnicalService:
    def __init__(self, analytics_service: AnalyticsService | None = None, market_service: MarketDataService | None = None):
        self.analytics_service = analytics_service or AnalyticsService()
        self.market_service = market_service or MarketDataService()

    def can_handle(self, router_result: RouterResult, query: str) -> bool:
        if router_result.intent != "technical_analysis":
            return False
        if not router_result.tickers:
            return False
        if router_result.need_news or router_result.need_reports or router_result.need_advice:
            return False
        spec = parse_indicator_spec(query, router_result.indicators, router_result.date_range)
        return spec is not None and spec.indicator in {"sma", "rsi", "return"}

    def handle(self, query: str, router_result: RouterResult) -> DirectTechnicalResult:
        ticker = router_result.tickers[0]
        spec = parse_indicator_spec(query, router_result.indicators, router_result.date_range)
        if spec is None:
            raise ValueError("unsupported indicator")

        t_latest = time.perf_counter()
        latest_date = self.analytics_service.get_latest_price_date(ticker)
        db_latest_date_ms = (time.perf_counter() - t_latest) * 1000
        base_key = f"indicator:{ticker}:{spec.indicator}:{spec.window}"
        cache_key = f"{base_key}:{latest_date}" if latest_date else base_key

        t_cache = time.perf_counter()
        cached = get_cached_value(cache_key)
        cache_ms = (time.perf_counter() - t_cache) * 1000
        if cached is not None:
            cached.cache_hit = True
            cached.cache_ms = cache_ms
            cached.db_latest_date_ms = db_latest_date_ms
            return cached

        required = self._required_points(spec)
        t_db = time.perf_counter()
        prices, fetched_latest_date = self.analytics_service.get_latest_close_prices(ticker, required)
        db_ms = (time.perf_counter() - t_db) * 1000
        latest = fetched_latest_date or latest_date or "N/A"

        warnings: list[str] = []
        evidence = [
            EvidenceItem(
                source="python_analytics_direct",
                source_type="analytics",
                ticker=ticker,
                date=latest,
                content=f"indicator={spec.indicator},window={spec.window},input_count={len(prices)},latest_price_date={latest}",
            )
        ]

        if self.market_service.is_stale(ticker):
            warnings.append("Price data is stale.")

        if not self._has_enough_data(spec, len(prices)):
            warnings.append("Insufficient price data for requested indicator.")
            result = DirectTechnicalResult(
                answer=f"Khong du du lieu de tinh {self._label(spec)} cho {ticker}.",
                evidence=evidence,
                warnings=warnings,
                cache_hit=False,
                indicator=spec.indicator,
                window=spec.window,
                cache_ms=cache_ms,
                db_ms=db_ms,
                db_latest_date_ms=db_latest_date_ms,
            )
            set_cached_value(cache_key, result, ttl_seconds=30)
            return result

        t_analytics = time.perf_counter()
        if spec.indicator == "sma":
            value = self.analytics_service.calculate_sma(prices, spec.window or 20)
            answer = f"{ticker}: SMA{spec.window or 20} = {value}."
        elif spec.indicator == "rsi":
            value = self.analytics_service.calculate_rsi(prices, spec.window or 14)
            answer = f"{ticker}: RSI{spec.window or 14} = {value}."
        else:
            value = self.analytics_service.calculate_return_pct(prices)
            answer = f"{ticker}: return {spec.window or 90} ngay = {value}%."
        analytics_ms = (time.perf_counter() - t_analytics) * 1000

        result = DirectTechnicalResult(
            answer=answer,
            evidence=evidence,
            warnings=warnings,
            cache_hit=False,
            indicator=spec.indicator,
            window=spec.window,
            cache_ms=cache_ms,
            db_ms=db_ms,
            db_latest_date_ms=db_latest_date_ms,
            analytics_ms=analytics_ms,
        )
        set_cached_value(cache_key, result, ttl_seconds=120)
        return result

    def _required_points(self, spec: IndicatorSpec) -> int:
        if spec.indicator == "sma":
            return max(spec.window or 20, 1)
        if spec.indicator == "rsi":
            return (spec.window or 14) + 1
        return spec.window or 90

    def _has_enough_data(self, spec: IndicatorSpec, count: int) -> bool:
        if spec.indicator == "sma":
            return count >= (spec.window or 20)
        if spec.indicator == "rsi":
            return count >= ((spec.window or 14) + 1)
        return count >= 2

    def _label(self, spec: IndicatorSpec) -> str:
        if spec.indicator == "sma":
            return f"SMA{spec.window or 20}"
        if spec.indicator == "rsi":
            return f"RSI{spec.window or 14}"
        return f"return {spec.window or 90} ngay"
