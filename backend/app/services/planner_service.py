from __future__ import annotations

import json
import os
import time

from app.services.router_scorer import RouterScoreResult, _intent_to_route
from app.runtime_diagnostics import get_request_diagnostics

ALLOWED_INTENTS = [
    "company_info",
    "market_data",
    "technical_analysis",
    "news_sentiment",
    "report_analysis",
    "investment_advisory",
    "forecast_outlook",
    "unknown",
]

ALLOWED_ROUTES = [
    "company_direct",
    "market_data_direct",
    "analytics_direct",
    "rag_light",
    "advisory_llm",
    "planner_fallback",
]


def _qwen_enabled() -> bool:
    return bool(os.getenv("QWEN_API_KEY", "").strip())


def _planner_prompt(query: str, scored: RouterScoreResult) -> str:
    return (
        "Classify the user query into allowed intent/route.\n"
        "Do not answer the finance question.\n"
        "Return JSON only.\n"
        f"Allowed intents: {ALLOWED_INTENTS}\n"
        f"Allowed routes: {ALLOWED_ROUTES}\n"
        f"User query: {query}\n"
        f"Scored top_intent={scored.top_intent}, second_intent={scored.second_intent}, margin={scored.margin}, time_context={scored.time_context}\n"
        'Output JSON: {"intent":"...","route":"...","reason":"..."}'
    )


def _call_qwen_classifier(prompt: str) -> dict | None:
    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=os.getenv("QWEN_API_KEY", "").strip(),
            base_url=os.getenv("QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1").strip(),
            timeout=float(os.getenv("QWEN_PLANNER_TIMEOUT_SECONDS", "4")),
        )
        model = os.getenv("QWEN_MODEL", "qwen-plus").strip()
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a routing classifier. Return JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
        )
        text = (resp.choices[0].message.content or "").strip() if resp.choices else ""
        if not text:
            return None
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start : end + 1]
        data = json.loads(text)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def planner_route_plan(query: str, scored: RouterScoreResult) -> dict:
    diag = get_request_diagnostics()
    t0 = time.perf_counter()
    timeout_used = False
    if _qwen_enabled():
        out = _call_qwen_classifier(_planner_prompt(query, scored))
        if diag is not None:
            diag.planner_ms = (time.perf_counter() - t0) * 1000
        if out:
            intent = str(out.get("intent") or scored.top_intent)
            route = str(out.get("route") or _intent_to_route(intent))
            if intent not in ALLOWED_INTENTS:
                intent = scored.top_intent
            if route not in ALLOWED_ROUTES:
                route = _intent_to_route(intent)
            return {"intent": intent, "route": route, "planner_used": True, "reason": str(out.get("reason") or "")}
        timeout_used = True
    if diag is not None:
        diag.planner_ms = (time.perf_counter() - t0) * 1000
        diag.timeout_used = diag.timeout_used or timeout_used
    return {
        "intent": scored.top_intent,
        "route": _intent_to_route(scored.top_intent),
        "planner_used": False,
        "reason": "fallback_to_scored_intent_or_planner_timeout",
    }
