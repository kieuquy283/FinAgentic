from app.schemas import EvidenceItem
from app.services.guardrails import apply_guardrails, get_disclaimer_policy


def test_empty_evidence_triggers_warning():
    g = apply_guardrails("investment_advisory", "advisory_llm", "demo answer", [], True)
    assert g.passed is False
    assert any("evidence" in w.lower() for w in g.warnings)


def test_disclaimer_exists_for_advisory():
    g = apply_guardrails("investment_advisory", "advisory_llm", "demo answer", [], False)
    assert "khuyến nghị" in g.disclaimer


def test_passed_true_when_evidence_exists():
    ev = [{
        "source": "sqlite",
        "source_type": "db",
        "ticker": "FPT",
        "date": "2026-05-14",
        "content": "facts"
    }]
    g = apply_guardrails("company_info", "company_direct", "demo answer", ev, False)
    assert g.passed is True


def test_runtime_stale_warning_propagates():
    ev = [EvidenceItem(source="sqlite", source_type="db", ticker="FPT", date="2026-05-14", content="facts")]
    g = apply_guardrails("market_data", "market_data_direct", "answer", ev, True, runtime_warnings=["Price data is stale."])
    assert any("stale" in w.lower() for w in g.warnings)


def test_guardrails_disclaimer_policy_by_intent():
    assert get_disclaimer_policy("company_info", "company_direct") == ""
    assert get_disclaimer_policy("market_data", "market_data_direct") == ""
    assert get_disclaimer_policy("technical_analysis", "analytics_direct") == ""
    assert "tham khảo" in get_disclaimer_policy("forecast_outlook", "advisory_llm")
    assert "khuyến nghị đầu tư cá nhân hóa" in get_disclaimer_policy("investment_advisory", "advisory_llm")
