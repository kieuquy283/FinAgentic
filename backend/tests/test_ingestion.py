import pandas as pd
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.db import ensure_runtime_tables, get_engine
from app.ingestion.ingestion_utils import match_ticker
from app.ingestion.market_ingestion import normalize_ohlcv, upsert_prices
from app.ingestion.news_ingestion import deduplicate_news, normalize_news_items
from app.main import app


def test_normalize_ohlcv_dataframe():
    df = pd.DataFrame(
        [
            {"date": "2026-01-02", "open": 10, "high": 12, "low": 9, "close": 11, "volume": 1000},
            {"date": "2026-01-03", "open": 11, "high": 13, "low": 10, "close": 12, "volume": 1200},
        ]
    )
    rows = normalize_ohlcv(df, "FPT", "vnstock", "https://example.com")
    assert len(rows) == 2
    assert rows[0].ticker == "FPT"
    assert rows[0].close == 11.0


def test_upsert_idempotency_prices():
    ensure_runtime_tables()
    df = pd.DataFrame([{"date": "2026-02-01", "open": 10, "high": 11, "low": 9, "close": 10.5, "volume": 900}])
    rows = normalize_ohlcv(df, "HPG", "vnstock", "https://example.com")
    upsert_prices(rows)
    upsert_prices(rows)
    engine = get_engine()
    with engine.connect() as conn:
        c = conn.execute(text("SELECT COUNT(*) as c FROM prices WHERE ticker='HPG' AND date='2026-02-01'")).mappings().first()["c"]
    assert c == 1


def test_news_deduplication():
    items = [
        {"title": "FPT tang truong", "url": "https://a", "snippet": "", "published_at": None, "source": "cafef"},
        {"title": "FPT tang truong", "url": "https://a", "snippet": "", "published_at": None, "source": "cafef"},
    ]
    dedup = deduplicate_news(items)
    assert len(dedup) == 1


def test_ticker_mapping_alias():
    assert match_ticker("Tin moi ve Vietcombank") == "VCB"
    assert match_ticker("hoa phat cong bo bao cao") == "HPG"


def test_normalize_news_items_ticker_filter():
    rows = normalize_news_items(
        [{"title": "FPT cong bo ket qua", "url": "https://x", "snippet": "tich cuc", "source": "cafef"}],
        ["FPT", "HPG"],
    )
    assert len(rows) == 1
    assert rows[0].ticker == "FPT"


def test_runtime_chat_no_external_api(monkeypatch):
    import app.ingestion.news_ingestion as ni

    def fail(*args, **kwargs):
        raise AssertionError("runtime should not call external fetchers")

    monkeypatch.setattr(ni.requests, "get", fail)
    client = TestClient(app)
    resp = client.post("/chat", json={"query": "FPT niem yet o san nao?"})
    assert resp.status_code == 200
