from __future__ import annotations

import contextvars
from dataclasses import dataclass, field


@dataclass
class RequestDiagnostics:
    direct_technical_used: bool = False
    aggregator_called: bool = False
    rag_called: bool = False
    ensure_fresh_called: bool = False
    refresh_if_needed_called: bool = False
    external_api_called: bool = False
    response_cache_hit: bool = False
    indicator_cache_hit: bool = False

    total_ms: float = 0.0
    route_ms: float = 0.0
    response_cache_ms: float = 0.0
    direct_technical_ms: float = 0.0
    indicator_cache_ms: float = 0.0
    db_latest_date_ms: float = 0.0
    db_prices_ms: float = 0.0
    analytics_ms: float = 0.0
    guardrails_ms: float = 0.0
    aggregator_ms: float = 0.0
    planner_ms: float = 0.0
    rag_ms: float = 0.0
    llm_ms: float = 0.0
    forecast_outlook_ms: float = 0.0
    fallback_used: bool = False
    timeout_used: bool = False
    horizon: str = ""


_DIAG_CTX: contextvars.ContextVar[RequestDiagnostics | None] = contextvars.ContextVar("request_diag", default=None)


def start_request_diagnostics() -> RequestDiagnostics:
    diag = RequestDiagnostics()
    _DIAG_CTX.set(diag)
    return diag


def get_request_diagnostics() -> RequestDiagnostics | None:
    return _DIAG_CTX.get()


def end_request_diagnostics() -> None:
    _DIAG_CTX.set(None)
