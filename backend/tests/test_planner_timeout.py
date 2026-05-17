from app.services import planner_service
from app.services.router_scorer import score_query


def test_planner_timeout_returns_safe_response(monkeypatch):
    scored = score_query("FPT 3 thang")
    monkeypatch.setattr(planner_service, "_qwen_enabled", lambda: True)
    monkeypatch.setattr(planner_service, "_call_qwen_classifier", lambda prompt: None)
    out = planner_service.planner_route_plan("FPT 3 thang", scored)
    assert out["intent"] == scored.top_intent
    assert out["route"] == planner_service._intent_to_route(scored.top_intent)
    assert out["planner_used"] is False
