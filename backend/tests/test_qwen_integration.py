from app.llm.prompts import SYSTEM_PROMPT
from app.llm.qwen_client import QwenClient
from app.schemas import AnalyticalContext, EvidenceItem
from app.services.advisory_service import AdvisoryService


def test_missing_qwen_api_key_uses_mock_fallback(monkeypatch):
    monkeypatch.delenv("QWEN_API_KEY", raising=False)
    c = QwenClient()
    out = c.synthesize("test")
    assert "Confidence: low" in out


def test_prompt_contains_disclaimer_instruction():
    assert "disclaimer" in SYSTEM_PROMPT.lower()
    assert "reference only" in SYSTEM_PROMPT.lower()


def test_advisory_service_passes_only_analytical_context(monkeypatch):
    captured = {"prompt": ""}

    def _fake_synthesize(self, user_prompt: str) -> str:
        captured["prompt"] = user_prompt
        return "ok"

    monkeypatch.setattr(QwenClient, "synthesize", _fake_synthesize)
    svc = AdvisoryService()
    ctx = AnalyticalContext(
        ticker="FPT",
        evidence=[
            EvidenceItem(
                source="vnstock",
                source_type="db",
                ticker="FPT",
                date="2026-05-14",
                content="close_latest=100, fetched_at=2026-05-14T01:00:00+00:00",
            )
        ],
    )
    out = svc.synthesize(ctx)
    assert out == "ok"
    assert "AnalyticalContext" in captured["prompt"]
    assert "SELECT " not in captured["prompt"]


def test_no_raw_dataframe_passed(monkeypatch):
    captured = {"prompt": ""}

    def _fake_synthesize(self, user_prompt: str) -> str:
        captured["prompt"] = user_prompt
        return "ok"

    monkeypatch.setattr(QwenClient, "synthesize", _fake_synthesize)
    svc = AdvisoryService()
    ctx = AnalyticalContext(ticker="HPG", evidence=[])
    svc.synthesize(ctx)
    assert "dataframe" not in captured["prompt"].lower()
