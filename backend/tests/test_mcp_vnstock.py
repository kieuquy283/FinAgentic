from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from app.db import ensure_runtime_tables, get_engine
from app.ingestion.freshness import is_price_stale, is_profile_stale
from app.ingestion.vnstock_ingestion import upsert_prices
from app.services.analytics_service import AnalyticsService
from app.services.market_data_service import MarketDataService
from app.tools.schemas import ToolResponse


def test_normalized_tool_output_shape():
    out = ToolResponse(
        fetched_at="2026-05-14T00:00:00+00:00",
        data_type="price_history",
        data=[{"ticker": "FPT", "date": "2026-05-14", "open": 1, "high": 2, "low": 1, "close": 2, "volume": 10, "source": "vnstock", "fetched_at": "2026-05-14T00:00:00+00:00"}],
        warnings=[],
    ).model_dump()
    assert out["source"] == "vnstock"
    assert out["data_type"] == "price_history"
    assert isinstance(out["data"], list)


def test_freshness_checks():
    assert is_price_stale("2020-01-01")
    assert not is_price_stale(datetime.now(timezone.utc).date().isoformat())
    assert is_profile_stale((datetime.now(timezone.utc) - timedelta(days=40)).isoformat())
    assert not is_profile_stale((datetime.now(timezone.utc) - timedelta(days=3)).isoformat())


def test_upsert_idempotency_prices_vnstock_ingestion():
    ensure_runtime_tables()
    rows = [{"ticker": "FPT", "date": "2026-01-01", "open": 10, "high": 11, "low": 9, "close": 10.5, "volume": 1000, "source": "vnstock", "fetched_at": "2026-05-14T00:00:00+00:00"}]
    upsert_prices(rows)
    upsert_prices(rows)
    with get_engine().connect() as conn:
        c = conn.execute(text("SELECT COUNT(*) c FROM prices WHERE ticker='FPT' AND date='2026-01-01'")).mappings().first()["c"]
    assert c == 1


def test_analytics_no_vnstock_direct_call():
    ensure_runtime_tables()
    svc = AnalyticsService()
    closes = svc.get_close_prices("FPT", 5)
    assert isinstance(closes, list)


def test_db_first_behavior(monkeypatch):
    ensure_runtime_tables()
    called = {"n": 0}

    def _fake_refresh(_ticker: str):
        called["n"] += 1
        return {"refreshed": False, "warnings": []}

    monkeypatch.setattr("app.services.market_data_service.refresh_if_needed", _fake_refresh)
    svc = MarketDataService()
    svc.ensure_fresh("FPT")
    assert called["n"] == 1

