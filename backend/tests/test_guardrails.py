from app.schemas import EvidenceItem
from app.services.guardrails import apply_guardrails


def test_empty_evidence_triggers_warning():
    g = apply_guardrails("investment_advisory", "demo answer", [], True)
    assert g.passed is False
    assert any("Thieu evidence" in w for w in g.warnings)


def test_disclaimer_exists_for_advisory():
    g = apply_guardrails("investment_advisory", "demo answer", [], False)
    assert "khuyen nghi" in g.disclaimer


def test_passed_true_when_evidence_exists():
    ev = [{
        "source": "sqlite",
        "source_type": "db",
        "ticker": "FPT",
        "date": "2026-05-14",
        "content": "facts"
    }]
    g = apply_guardrails("company_info", "demo answer", ev, False)
    assert g.passed is True


def test_runtime_stale_warning_propagates():
    ev = [EvidenceItem(source="sqlite", source_type="db", ticker="FPT", date="2026-05-14", content="facts")]
    g = apply_guardrails("market_data", "answer", ev, True, runtime_warnings=["Price data is stale."])
    assert any("stale" in w.lower() for w in g.warnings)
