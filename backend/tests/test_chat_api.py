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
    assert "Chua hieu ro cau hoi" in data["answer"]


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
