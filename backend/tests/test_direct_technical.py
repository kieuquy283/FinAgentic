import pytest
from fastapi.testclient import TestClient

from app.cache import clear_all_caches
from app.db import get_engine
from app.main import app
from app.services.analytics_service import AnalyticsService
from app.services.direct_technical_service import DirectTechnicalService
from app.services.evidence_aggregator import EvidenceAggregator
from app.services.market_data_service import MarketDataService
from app.services.rag_service import RagService
from app.services.router_scorer import parse_indicator_spec


client = TestClient(app)


@pytest.fixture(autouse=True)
def _clear_cache():
    clear_all_caches()
    yield
    clear_all_caches()


def test_direct_sma_path_does_not_call_aggregator(monkeypatch):
    called = {"agg": 0}

    def _boom(self, ticker: str, query: str):
        called["agg"] += 1
        raise AssertionError("aggregator should not be called")

    monkeypatch.setattr(EvidenceAggregator, "build", _boom)
    resp = client.post("/chat", json={"query": "SMA20 FPT"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "technical_analysis"
    assert "SMA20" in data["answer"]
    assert called["agg"] == 0


def test_sma20_query_returns_answer():
    resp = client.post("/chat", json={"query": "calculate SMA for FPT"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "technical_analysis"
    assert "SMA" in data["answer"]


def test_rsi14_query_returns_answer():
    resp = client.post("/chat", json={"query": "RSI14 for HPG"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "technical_analysis"
    assert "RSI14" in data["answer"]


def test_direct_path_skips_rag(monkeypatch):
    def _boom(self, ticker: str, query: str, top_k: int = 5):
        raise AssertionError("rag should not be called")

    monkeypatch.setattr(RagService, "search", _boom)
    resp = client.post("/chat", json={"query": "RSI14 FPT"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "technical_analysis"


def test_indicator_cache_hit():
    class FakeAnalytics(AnalyticsService):
        def __init__(self):
            self.calls = 0

        def get_latest_price_date(self, ticker: str):
            return "2026-05-14"

        def get_latest_close_prices(self, ticker: str, limit: int):
            self.calls += 1
            prices = [float(i) for i in range(1, limit + 1)]
            return prices, "2026-05-14"

    svc_analytics = FakeAnalytics()
    svc = DirectTechnicalService(analytics_service=svc_analytics, market_service=MarketDataService())

    from app.schemas import RouterResult

    router = RouterResult(
        intent="technical_analysis",
        tickers=["FPT"],
        indicators=["SMA"],
        route="analytics_direct",
        confidence="high",
    )

    first = svc.handle("SMA20 FPT", router)
    second = svc.handle("SMA20 FPT", router)
    assert "SMA20" in first.answer
    assert second.cache_hit is True
    assert svc_analytics.calls == 1


def test_get_engine_singleton():
    e1 = get_engine()
    e2 = get_engine()
    assert e1 is e2


def test_not_enough_prices_returns_safe_warning(monkeypatch):
    class LowDataAnalytics(AnalyticsService):
        def get_latest_price_date(self, ticker: str):
            return "2026-05-14"

        def get_latest_close_prices(self, ticker: str, limit: int):
            return [1.0, 2.0], "2026-05-14"

    from app.schemas import RouterResult

    svc = DirectTechnicalService(analytics_service=LowDataAnalytics(), market_service=MarketDataService())
    router = RouterResult(
        intent="technical_analysis",
        tickers=["FPT"],
        indicators=["SMA"],
        route="analytics_direct",
        confidence="high",
    )
    result = svc.handle("SMA20 FPT", router)
    assert "Khong du du lieu" in result.answer
    assert any("Insufficient" in w for w in result.warnings)


def test_indicator_parser_defaults_and_windows():
    s1 = parse_indicator_spec("SMA20 FPT")
    s2 = parse_indicator_spec("sma for fpt")
    s3 = parse_indicator_spec("RSI14 for HPG")
    s4 = parse_indicator_spec("RSI for HPG")
    assert s1 and s1.indicator == "sma" and s1.window == 20
    assert s2 and s2.indicator == "sma" and s2.window == 20
    assert s3 and s3.indicator == "rsi" and s3.window == 14
    assert s4 and s4.indicator == "rsi" and s4.window == 14


def test_direct_path_does_not_call_ensure_fresh(monkeypatch):
    def _boom(self, ticker: str):
        raise AssertionError("ensure_fresh should not be called")

    monkeypatch.setattr(MarketDataService, "ensure_fresh", _boom)
    resp = client.post("/chat", json={"query": "SMA20 FPT"})
    assert resp.status_code == 200
