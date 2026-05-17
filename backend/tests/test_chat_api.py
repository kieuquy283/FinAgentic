from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_empty_query_returns_safe_response():
    resp = client.post("/chat", json={"query": "   "})
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "unknown"
    assert data["route"] == "unknown"
    assert data["confidence"] == "low"
    assert "Vui long nhap cau hoi" in data["answer"]
    assert "disclaimer" in data["guardrails"]


def test_unknown_intent_returns_fallback():
    resp = client.post("/chat", json={"query": "Toi muon hoi cau nay la gi?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "unknown"
    assert data["route"] == "unknown"
    assert data["confidence"] in ["low", "medium", "high"]
    assert "Minh chua du thong tin" in data["answer"] or "Mình chưa đủ thông tin" in data["answer"]


def test_missing_ticker_returns_clear_error():
    resp = client.post("/chat", json={"query": "Gia 3 thang gan day the nao?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "market_data"
    assert data["confidence"] == "low"
    assert "Khong tim thay ticker hop le" in data["answer"]


def test_db_failure_returns_safe_error(monkeypatch):
    from app.services.evidence_aggregator import EvidenceAggregator

    def _boom(self, ticker: str, query: str):
        raise RuntimeError("db down")

    monkeypatch.setattr(EvidenceAggregator, "build", _boom)
    resp = client.post("/chat", json={"query": "FPT niem yet o san nao?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["confidence"] == "low"
    assert "He thong du lieu chua san sang" in data["answer"]


def test_sma20_direct_path_skips_aggregator_and_network(monkeypatch):
    from app.services.evidence_aggregator import EvidenceAggregator
    from app.services.rag_service import RagService
    from app.services.advisory_service import AdvisoryService

    def _boom(*args, **kwargs):
        raise AssertionError("should not be called for direct technical path")

    monkeypatch.setattr(EvidenceAggregator, "build", _boom)
    monkeypatch.setattr(RagService, "search", _boom)
    monkeypatch.setattr(AdvisoryService, "synthesize", _boom)

    resp = client.post("/chat", json={"query": "SMA20 FPT"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "technical_analysis"
    assert "direct" in data["route"]
    assert "SMA20" in data["answer"]


def test_healthz_includes_database_diagnostics():
    resp = client.get("/healthz")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "uptime_seconds" in data
    assert "database" in data
    assert "dialect" in data["database"]
    assert "connection_ok" in data["database"]
    assert "target" in data["database"]
    assert "prices_table_exists" in data["database"]
    assert "idx_prices_ticker_date" in data["database"]


def test_unknown_query_returns_fast_without_aggregator(monkeypatch):
    import time
    from app.services.evidence_aggregator import EvidenceAggregator

    def _boom(*args, **kwargs):
        raise AssertionError("aggregator should not be called for unknown")

    monkeypatch.setattr(EvidenceAggregator, "build", _boom)
    t0 = time.perf_counter()
    resp = client.post("/chat", json={"query": "xin chao ban"})
    elapsed_ms = (time.perf_counter() - t0) * 1000
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "unknown"
    assert elapsed_ms < 100


def test_unknown_query_does_not_call_rag_or_llm(monkeypatch):
    from app.services.rag_service import RagService
    from app.services.advisory_service import AdvisoryService

    def _boom(*args, **kwargs):
        raise AssertionError("should not be called for unknown")

    monkeypatch.setattr(RagService, "search", _boom)
    monkeypatch.setattr(AdvisoryService, "synthesize", _boom)

    resp = client.post("/chat", json={"query": "alo alo"})
    assert resp.status_code == 200
    assert resp.json()["intent"] == "unknown"


def test_planner_timeout_returns_safe_response(monkeypatch):
    from app.llm.qwen_client import QwenClient

    monkeypatch.setenv("QWEN_API_KEY", "dummy-key")

    def _timeout(self, user_prompt: str):
        raise TimeoutError("planner timeout")

    monkeypatch.setattr(QwenClient, "_call_qwen", _timeout)
    resp = client.post("/chat", json={"query": "FPT co nen mua khong?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] in ["investment_advisory", "forecast_outlook"]
    assert "Disclaimer" in data["answer"] or "disclaimer" in data["answer"].lower()


def test_forecast_answer_contains_risks_and_disclaimer():
    resp = client.post("/chat", json={"query": "dự kiến tình hình của FPT trong 1 tháng tới"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "forecast_outlook"
    assert "Rui ro" in data["answer"] or "rui ro" in data["answer"].lower()
    assert "disclaimer" in data["guardrails"]


def test_forecast_does_not_claim_exact_future_price():
    resp = client.post("/chat", json={"query": "dự đoán giá FPT tháng tới"})
    assert resp.status_code == 200
    text = resp.json()["answer"].lower()
    assert "gia dich den" not in text
    assert "gia cu the" not in text


def test_direct_sma_path_still_fast_and_unchanged():
    resp = client.post("/chat", json={"query": "SMA20 FPT"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "technical_analysis"
    assert "direct" in data["route"]
    assert "SMA20" in data["answer"]


def test_technical_answer_is_natural_and_contains_indicator_explanation():
    resp = client.post("/chat", json={"query": "SMA20 FPT"})
    assert resp.status_code == 200
    text = resp.json()["answer"]
    assert "SMA20 cua FPT" in text or "SMA20 của FPT" in text
    assert "trung binh" in text.lower() or "trung bình" in text.lower()


def test_market_summary_answer_does_not_predict_future():
    resp = client.post("/chat", json={"query": "tinh hinh FPT 3 thang gan day"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "market_data"
    text = data["answer"].lower()
    assert "khong phai du bao gia tuong lai" in text


def test_unknown_answer_is_fast_and_human_readable():
    import time

    t0 = time.perf_counter()
    resp = client.post("/chat", json={"query": "abcxyz ???"})
    elapsed_ms = (time.perf_counter() - t0) * 1000
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "unknown"
    assert "Minh chua du thong tin" in data["answer"] or "Mình chưa đủ thông tin" in data["answer"]
    assert elapsed_ms < 100


def test_answer_composer_does_not_change_chatresponse_contract():
    resp = client.post("/chat", json={"query": "SMA20 FPT"})
    assert resp.status_code == 200
    data = resp.json()
    for k in ["query", "intent", "route", "answer", "evidence", "confidence", "guardrails", "latency_ms"]:
        assert k in data
