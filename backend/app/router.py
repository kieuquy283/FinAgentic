from __future__ import annotations

import time

from app.schemas import RouterResult
from app.runtime_diagnostics import get_request_diagnostics
from app.services.planner_service import planner_route_plan
from app.services.router_scorer import score_query


def route_query(query: str) -> RouterResult:
    scored = score_query(query)
    intent = scored.intent
    route = scored.route
    needs_planner = scored.needs_planner
    if needs_planner:
        t0 = time.perf_counter()
        plan = planner_route_plan(query, scored)
        diag = get_request_diagnostics()
        if diag is not None and diag.planner_ms == 0.0:
            diag.planner_ms = (time.perf_counter() - t0) * 1000
        intent = str(plan.get("intent") or intent)
        route = str(plan.get("route") or route)

    window_size = 14 if "RSI" in scored.indicators else (20 if "SMA" in scored.indicators else None)
    confidence = "high" if scored.confidence >= 0.80 else ("medium" if scored.confidence >= 0.65 else "low")

    return RouterResult(
        intent=intent,
        tickers=scored.tickers,
        date_range=scored.date_range,
        indicators=scored.indicators,
        window_size=window_size,
        need_news=intent in ["news_sentiment", "investment_advisory", "forecast_outlook", "report_analysis"],
        need_reports=intent in ["news_sentiment", "investment_advisory", "report_analysis", "forecast_outlook"],
        need_advice=intent in ["investment_advisory", "forecast_outlook"],
        confidence=confidence,
        route=route,
        scores=scored.scores,
        top_intent=scored.top_intent,
        second_intent=scored.second_intent,
        margin=scored.margin,
        time_context=scored.time_context,
        needs_planner=needs_planner,
        matched_keywords=scored.matched_keywords,
    )
