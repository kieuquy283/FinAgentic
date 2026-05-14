from fastapi.testclient import TestClient

from app.main import app
from app import scheduler as sched


def test_scheduler_disabled_by_env(monkeypatch):
    sched.stop_daily_refresh_scheduler()
    monkeypatch.setenv("DAILY_REFRESH_ENABLED", "false")
    started = sched.start_daily_refresh_scheduler()
    assert started is False


def test_refresh_continues_when_one_ticker_fails(monkeypatch):
    calls = []

    def _fake_ingest(ticker: str, do_all: bool = False, **kwargs):
        calls.append(ticker)
        if ticker == "HPG":
            raise RuntimeError("boom")
        return {"ticker": ticker, "prices": 1, "profile": 1, "ratios": 1, "warnings": []}

    monkeypatch.setattr(sched, "ingest_ticker_data", _fake_ingest)
    out = sched.run_refresh_job(["FPT", "HPG", "VCB"])
    assert out["ok"] == 2
    assert out["failed"] == 1
    assert calls == ["FPT", "HPG", "VCB"]


def test_refresh_status_endpoint_shape(monkeypatch):
    client = TestClient(app)
    monkeypatch.setattr(
        sched,
        "refresh_status",
        lambda: {
            "scheduler_enabled": True,
            "last_successful_refresh": None,
            "last_failed_refresh": None,
            "latest_data_date_by_ticker": {},
            "tickers": ["FPT"],
            "timezone": "Asia/Ho_Chi_Minh",
            "last_job_summary": None,
        },
    )
    resp = client.get("/admin/refresh-status")
    assert resp.status_code == 200
    data = resp.json()
    assert "scheduler_enabled" in data
    assert "last_successful_refresh" in data
    assert "last_failed_refresh" in data
    assert "latest_data_date_by_ticker" in data

