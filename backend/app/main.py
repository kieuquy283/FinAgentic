from __future__ import annotations

import os
import time
import logging
import subprocess
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

from sqlalchemy import text

from app.cache import get_cache, normalize_query, set_cache
from app.router import route_query
from app import scheduler as scheduler_mod
from app.db import (
    DB_PATH,
    ensure_prices_index,
    ensure_runtime_tables,
    get_database_target_public,
    get_db_dialect,
    get_engine,
    has_prices_index,
    table_exists,
)
from app.runtime_diagnostics import end_request_diagnostics, start_request_diagnostics
from app.schemas import ChatRequest, ChatResponse, EvidenceItem
from app.services.advisory_service import AdvisoryService
from app.services.answer_composer import AnswerComposer
from app.services.direct_technical_service import DirectTechnicalService
from app.services.evidence_aggregator import EvidenceAggregator
from app.services.forecast_outlook_service import ForecastOutlookService, parse_forecast_horizon
from app.services.guardrails import DISCLAIMER, apply_guardrails

logger = logging.getLogger(__name__)
APP_START_TS = time.time()


def _cors_origins() -> list[str]:
    origins = {"http://localhost:5173"}
    single = os.getenv("FRONTEND_ORIGIN", "").strip()
    if single:
        origins.add(single)
    many = os.getenv("FRONTEND_ORIGINS", "").strip()
    if many:
        for item in many.split(","):
            val = item.strip()
            if val:
                origins.add(val)
    return sorted(origins)


def _safe_response(query: str, intent: str, route: str, answer: str, warnings: list[str], latency_ms: int) -> ChatResponse:
    return ChatResponse(
        query=query,
        intent=intent,
        route=route,
        answer=f"{answer}\n{DISCLAIMER}",
        evidence=[],
        confidence="low",
        guardrails={
            "passed": False,
            "warnings": warnings,
            "disclaimer": DISCLAIMER,
        },
        latency_ms=latency_ms,
    )


def _log_request_summary(
    query: str,
    intent: str,
    route: str,
    tickers: list[str],
    diag,
) -> None:
    logger.info(
        "chat_path query=%s intent=%s route=%s tickers=%s horizon=%s route_ms=%.2f planner_ms=%.2f forecast_outlook_ms=%.2f aggregator_ms=%.2f rag_ms=%.2f llm_ms=%.2f total_ms=%.2f fallback_used=%s timeout_used=%s",
        query,
        intent,
        route,
        tickers,
        getattr(diag, "horizon", ""),
        diag.route_ms,
        diag.planner_ms,
        diag.forecast_outlook_ms,
        diag.aggregator_ms,
        diag.rag_ms,
        diag.llm_ms,
        diag.total_ms,
        diag.fallback_used,
        diag.timeout_used,
    )


app = FastAPI(title="FinAgentic")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/healthz")
def healthz():
    db_ok = True
    prices_count = None
    prices_exists = False
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1")).scalar()
            prices_exists = table_exists("prices")
            if prices_exists:
                row = conn.execute(text("SELECT COUNT(*) AS c FROM prices")).mappings().first()
                prices_count = int(row["c"]) if row else 0
    except Exception:
        db_ok = False
    return {
        "status": "ok" if db_ok else "degraded",
        "uptime_seconds": round(time.time() - APP_START_TS, 3),
        "database": {
            "dialect": get_db_dialect(),
            "connection_ok": db_ok,
            "target": get_database_target_public(),
            "prices_table_exists": prices_exists,
            "prices_count": prices_count,
            "idx_prices_ticker_date": has_prices_index() if db_ok else False,
        },
    }


@app.get("/warmup")
def warmup():
    engine = get_engine()
    t0 = time.perf_counter()
    with engine.connect() as conn:
        conn.execute(text("SELECT 1")).scalar()
        row = conn.execute(
            text("SELECT date, close FROM prices WHERE ticker=:ticker ORDER BY date DESC LIMIT 1"),
            {"ticker": "FPT"},
        ).mappings().first()
    return {
        "status": "ok",
        "uptime_s": round(time.time() - APP_START_TS, 3),
        "db_ping_ms": round((time.perf_counter() - t0) * 1000, 3),
        "fpt_latest_date": str(row["date"]) if row else None,
        "index_present": has_prices_index(),
    }


@app.get("/")
def root():
    return {"status": "ok", "app": "FinAgentic"}


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)


class RefreshRequest(BaseModel):
    tickers: list[str] | None = None


@app.on_event("startup")
def startup_event() -> None:
    ensure_runtime_tables()
    ensure_prices_index()
    db_exists = DB_PATH.exists()
    db_size = DB_PATH.stat().st_size if db_exists else 0
    commit = "unknown"
    try:
        commit = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:
        pass
    logger.info(
        "startup ts=%s db_path=%s db_exists=%s db_size_bytes=%s git_commit=%s idx_prices_ticker_date=%s",
        datetime.now(timezone.utc).isoformat(),
        str(DB_PATH),
        db_exists,
        db_size,
        commit,
        has_prices_index(),
    )
    try:
        scheduler_mod.start_daily_refresh_scheduler()
    except Exception:
        # Never block API startup
        pass


@app.on_event("shutdown")
def shutdown_event() -> None:
    try:
        scheduler_mod.stop_daily_refresh_scheduler()
    except Exception:
        pass


@app.post("/admin/refresh-data")
def admin_refresh_data(req: RefreshRequest | None = None):
    tickers = req.tickers if req else None
    try:
        return scheduler_mod.run_refresh_job(tickers=tickers)
    except Exception as exc:  # noqa: BLE001
        return {"job": "daily_refresh", "status": "error", "message": str(exc)}


@app.get("/admin/refresh-status")
def admin_refresh_status():
    return scheduler_mod.refresh_status()


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    start = time.perf_counter()
    diag = start_request_diagnostics()
    query = req.query.strip()
    if not query:
        resp = _safe_response(
            query=req.query,
            intent="unknown",
            route="unknown",
            answer="Vui long nhap cau hoi co ticker, vi du: FPT niem yet o san nao?",
            warnings=["Cau hoi rong.", "Du lieu dang o che do demo/mock."],
            latency_ms=int((time.perf_counter() - start) * 1000),
        )
        diag.total_ms = (time.perf_counter() - start) * 1000
        diag.fallback_used = True
        _log_request_summary(query=query, intent="unknown", route="unknown", tickers=[], diag=diag)
        logger.info(
            "chat_diag total_ms=%.2f route_ms=%.2f response_cache_ms=%.2f direct_technical_ms=%.2f indicator_cache_ms=%.2f db_latest_date_ms=%.2f db_prices_ms=%.2f analytics_ms=%.2f guardrails_ms=%.2f aggregator_ms=%.2f direct_technical_used=%s aggregator_called=%s rag_called=%s ensure_fresh_called=%s refresh_if_needed_called=%s external_api_called=%s response_cache_hit=%s indicator_cache_hit=%s",
            diag.total_ms, diag.route_ms, diag.response_cache_ms, diag.direct_technical_ms, diag.indicator_cache_ms,
            diag.db_latest_date_ms, diag.db_prices_ms, diag.analytics_ms, diag.guardrails_ms, diag.aggregator_ms,
            diag.direct_technical_used, diag.aggregator_called, diag.rag_called, diag.ensure_fresh_called,
            diag.refresh_if_needed_called, diag.external_api_called, diag.response_cache_hit, diag.indicator_cache_hit,
        )
        end_request_diagnostics()
        return resp

    key = normalize_query(query)
    t_cache = time.perf_counter()
    cached = get_cache(key)
    diag.response_cache_ms = (time.perf_counter() - t_cache) * 1000
    if cached is not None:
        diag.response_cache_hit = True
        ev = list(cached.evidence)
        ev.append(
            EvidenceItem(
                source="in_memory_cache",
                source_type="cache",
                ticker=ev[0].ticker if ev else "N/A",
                date="2026-05-14",
                content="cache_hit",
            )
        )
        resp = ChatResponse(
            query=cached.query,
            intent=cached.intent,
            route=cached.route,
            answer=cached.answer,
            evidence=ev,
            confidence=cached.confidence,
            guardrails=cached.guardrails,
            latency_ms=int((time.perf_counter() - start) * 1000),
        )
        diag.total_ms = (time.perf_counter() - start) * 1000
        _log_request_summary(query=query, intent=cached.intent, route=cached.route, tickers=[ev[0].ticker] if ev else [], diag=diag)
        logger.info(
            "chat_diag total_ms=%.2f route_ms=%.2f response_cache_ms=%.2f direct_technical_ms=%.2f indicator_cache_ms=%.2f db_latest_date_ms=%.2f db_prices_ms=%.2f analytics_ms=%.2f guardrails_ms=%.2f aggregator_ms=%.2f direct_technical_used=%s aggregator_called=%s rag_called=%s ensure_fresh_called=%s refresh_if_needed_called=%s external_api_called=%s response_cache_hit=%s indicator_cache_hit=%s",
            diag.total_ms, diag.route_ms, diag.response_cache_ms, diag.direct_technical_ms, diag.indicator_cache_ms,
            diag.db_latest_date_ms, diag.db_prices_ms, diag.analytics_ms, diag.guardrails_ms, diag.aggregator_ms,
            diag.direct_technical_used, diag.aggregator_called, diag.rag_called, diag.ensure_fresh_called,
            diag.refresh_if_needed_called, diag.external_api_called, diag.response_cache_hit, diag.indicator_cache_hit,
        )
        end_request_diagnostics()
        return resp

    t_route = time.perf_counter()
    router_result = route_query(query)
    diag.route_ms = (time.perf_counter() - t_route) * 1000
    ticker = router_result.tickers[0] if router_result.tickers else ""
    diag.horizon = parse_forecast_horizon(query, router_result.date_range) if router_result.intent == "forecast_outlook" else ""
    if router_result.intent == "unknown":
        composer = AnswerComposer()
        resp = _safe_response(
            query=query,
            intent="unknown",
            route="unknown",
            answer=composer.compose_unknown_answer(),
            warnings=["Y nghia cau hoi chua ro.", "Du lieu dang o che do demo/mock."],
            latency_ms=int((time.perf_counter() - start) * 1000),
        )
        diag.fallback_used = True
        diag.total_ms = (time.perf_counter() - start) * 1000
        _log_request_summary(query=query, intent="unknown", route="unknown", tickers=router_result.tickers, diag=diag)
        end_request_diagnostics()
        return resp

    if router_result.intent != "unknown" and not ticker:
        resp = _safe_response(
            query=query,
            intent=router_result.intent,
            route=router_result.route,
            answer="Khong tim thay ticker hop le. Vui long dung ma co phieu nhu FPT, HPG, VCB, VNM.",
            warnings=["Thieu ticker trong cau hoi.", "Du lieu dang o che do demo/mock."],
            latency_ms=int((time.perf_counter() - start) * 1000),
        )
        diag.total_ms = (time.perf_counter() - start) * 1000
        diag.fallback_used = True
        _log_request_summary(query=query, intent=router_result.intent, route=router_result.route, tickers=router_result.tickers, diag=diag)
        logger.info(
            "chat_diag total_ms=%.2f route_ms=%.2f response_cache_ms=%.2f direct_technical_ms=%.2f indicator_cache_ms=%.2f db_latest_date_ms=%.2f db_prices_ms=%.2f analytics_ms=%.2f guardrails_ms=%.2f aggregator_ms=%.2f direct_technical_used=%s aggregator_called=%s rag_called=%s ensure_fresh_called=%s refresh_if_needed_called=%s external_api_called=%s response_cache_hit=%s indicator_cache_hit=%s",
            diag.total_ms, diag.route_ms, diag.response_cache_ms, diag.direct_technical_ms, diag.indicator_cache_ms,
            diag.db_latest_date_ms, diag.db_prices_ms, diag.analytics_ms, diag.guardrails_ms, diag.aggregator_ms,
            diag.direct_technical_used, diag.aggregator_called, diag.rag_called, diag.ensure_fresh_called,
            diag.refresh_if_needed_called, diag.external_api_called, diag.response_cache_hit, diag.indicator_cache_hit,
        )
        end_request_diagnostics()
        return resp

    direct_service = DirectTechnicalService()
    composer = AnswerComposer()
    if direct_service.can_handle(router_result, query):
        diag.direct_technical_used = True
        t_direct = time.perf_counter()
        direct_result = direct_service.handle(query=query, router_result=router_result)
        diag.direct_technical_ms = (time.perf_counter() - t_direct) * 1000
        diag.indicator_cache_ms = direct_result.cache_ms
        diag.db_latest_date_ms = direct_result.db_latest_date_ms
        diag.db_prices_ms = direct_result.db_ms
        diag.analytics_ms = direct_result.analytics_ms
        diag.indicator_cache_hit = direct_result.cache_hit

        latest_date = direct_result.evidence[0].date if direct_result.evidence else None
        natural_answer = composer.compose_technical_answer(
            ticker=ticker,
            raw_answer=direct_result.answer,
            latest_price_date=latest_date,
        )
        t_guard = time.perf_counter()
        guard = apply_guardrails(
            intent=router_result.intent,
            answer=natural_answer,
            evidence=direct_result.evidence,
            has_numeric=True,
            demo_fallback=False,
            runtime_warnings=direct_result.warnings,
        )
        diag.guardrails_ms = (time.perf_counter() - t_guard) * 1000
        conf = router_result.confidence if guard.passed else "low"
        response = ChatResponse(
            query=req.query,
            intent=router_result.intent,
            route=router_result.route,
            answer=f"{natural_answer}\n{guard.disclaimer}",
            evidence=direct_result.evidence,
            confidence=conf,
            guardrails=guard,
            latency_ms=int((time.perf_counter() - start) * 1000),
        )
        set_cache(key, response)
        diag.total_ms = (time.perf_counter() - start) * 1000
        _log_request_summary(query=query, intent=router_result.intent, route=router_result.route, tickers=router_result.tickers, diag=diag)
        logger.info(
            "chat_diag total_ms=%.2f route_ms=%.2f response_cache_ms=%.2f direct_technical_ms=%.2f indicator_cache_ms=%.2f db_latest_date_ms=%.2f db_prices_ms=%.2f analytics_ms=%.2f guardrails_ms=%.2f aggregator_ms=%.2f direct_technical_used=%s aggregator_called=%s rag_called=%s ensure_fresh_called=%s refresh_if_needed_called=%s external_api_called=%s response_cache_hit=%s indicator_cache_hit=%s",
            diag.total_ms, diag.route_ms, diag.response_cache_ms, diag.direct_technical_ms, diag.indicator_cache_ms,
            diag.db_latest_date_ms, diag.db_prices_ms, diag.analytics_ms, diag.guardrails_ms, diag.aggregator_ms,
            diag.direct_technical_used, diag.aggregator_called, diag.rag_called, diag.ensure_fresh_called,
            diag.refresh_if_needed_called, diag.external_api_called, diag.response_cache_hit, diag.indicator_cache_hit,
        )
        end_request_diagnostics()
        return response

    aggregator = EvidenceAggregator()
    advisory = AdvisoryService()
    forecast_service = ForecastOutlookService()
    try:
        diag.aggregator_called = True
        t_agg = time.perf_counter()
        ctx = aggregator.build(ticker=ticker, query=query)
        diag.aggregator_ms = (time.perf_counter() - t_agg) * 1000
    except Exception:
        resp = _safe_response(
            query=query,
            intent=router_result.intent,
            route=router_result.route,
            answer="He thong du lieu chua san sang. Vui long chay lai script seed du lieu backend.",
            warnings=["Khong the truy cap CSDL du lieu demo.", "Du lieu dang o che do demo/mock."],
            latency_ms=int((time.perf_counter() - start) * 1000),
        )
        diag.total_ms = (time.perf_counter() - start) * 1000
        diag.fallback_used = True
        _log_request_summary(query=query, intent=router_result.intent, route=router_result.route, tickers=router_result.tickers, diag=diag)
        logger.info(
            "chat_diag total_ms=%.2f route_ms=%.2f response_cache_ms=%.2f direct_technical_ms=%.2f indicator_cache_ms=%.2f db_latest_date_ms=%.2f db_prices_ms=%.2f analytics_ms=%.2f guardrails_ms=%.2f aggregator_ms=%.2f direct_technical_used=%s aggregator_called=%s rag_called=%s ensure_fresh_called=%s refresh_if_needed_called=%s external_api_called=%s response_cache_hit=%s indicator_cache_hit=%s",
            diag.total_ms, diag.route_ms, diag.response_cache_ms, diag.direct_technical_ms, diag.indicator_cache_ms,
            diag.db_latest_date_ms, diag.db_prices_ms, diag.analytics_ms, diag.guardrails_ms, diag.aggregator_ms,
            diag.direct_technical_used, diag.aggregator_called, diag.rag_called, diag.ensure_fresh_called,
            diag.refresh_if_needed_called, diag.external_api_called, diag.response_cache_hit, diag.indicator_cache_hit,
        )
        end_request_diagnostics()
        return resp

    if router_result.intent == "company_info" and ctx.company_snapshot:
        answer = composer.compose_company_info_answer(ctx.company_snapshot)
    elif router_result.intent == "market_data" and ctx.market_snapshot:
        answer = composer.compose_market_summary_answer(ticker=ticker, market=ctx.market_snapshot)
    elif router_result.intent == "technical_analysis" and ctx.technical_snapshot:
        t = ctx.technical_snapshot
        answer = (
            f"RSI14 cua {ticker} hien o muc {t.rsi14}, SMA20 khoang {t.sma20}, "
            f"hieu suat ky gan day {t.return_pct}%. Day la bo chi bao ky thuat de tham khao xu huong ngan han."
        )
    elif router_result.intent == "news_sentiment" and ctx.news_snapshot:
        answer = f"Tin tuc gan day ve {ticker} nghieng ve {ctx.news_snapshot.sentiment}."
    elif router_result.intent == "investment_advisory":
        answer = advisory.synthesize(ctx)
    elif router_result.intent == "forecast_outlook":
        horizon = parse_forecast_horizon(query, router_result.date_range)
        forecast = forecast_service.synthesize(
            ticker=ticker,
            query=query,
            horizon=horizon,
            router_result=router_result,
            ctx=ctx,
        )
        answer = composer.compose_forecast_outlook_answer(
            ticker=ticker,
            horizon=horizon,
            ctx=ctx,
            draft=forecast.answer,
        )
    else:
        answer = composer.compose_unknown_answer()
        diag.fallback_used = True

    t_guard = time.perf_counter()
    guard = apply_guardrails(
        intent=router_result.intent,
        answer=answer,
        evidence=ctx.evidence,
        has_numeric=router_result.intent in ["market_data", "technical_analysis", "investment_advisory"],
        runtime_warnings=ctx.runtime_warnings,
        demo_fallback=(
            any(
                marker in (e.source or "").lower()
                for e in ctx.evidence
                for marker in ["demo_seed", "local_seed", "fallback_static_metadata", "unknown", "sqlite_prices", "sqlite_companies"]
            )
            or (
                router_result.intent in ["market_data", "technical_analysis", "news_sentiment", "investment_advisory"]
                and not any(src in (e.source or "").lower() for e in ctx.evidence for src in ["vnstock", "cafef"])
            )
        ),
    )
    diag.guardrails_ms = (time.perf_counter() - t_guard) * 1000
    conf = router_result.confidence if guard.passed else "low"

    response = ChatResponse(
        query=req.query,
        intent=router_result.intent,
        route=router_result.route,
        answer=f"{answer}\n{guard.disclaimer}",
        evidence=ctx.evidence,
        confidence=conf,
        guardrails=guard,
        latency_ms=int((time.perf_counter() - start) * 1000),
    )

    set_cache(key, response)
    diag.total_ms = (time.perf_counter() - start) * 1000
    _log_request_summary(query=query, intent=router_result.intent, route=router_result.route, tickers=router_result.tickers, diag=diag)
    logger.info(
        "chat_diag total_ms=%.2f route_ms=%.2f response_cache_ms=%.2f direct_technical_ms=%.2f indicator_cache_ms=%.2f db_latest_date_ms=%.2f db_prices_ms=%.2f analytics_ms=%.2f guardrails_ms=%.2f aggregator_ms=%.2f direct_technical_used=%s aggregator_called=%s rag_called=%s ensure_fresh_called=%s refresh_if_needed_called=%s external_api_called=%s response_cache_hit=%s indicator_cache_hit=%s",
        diag.total_ms, diag.route_ms, diag.response_cache_ms, diag.direct_technical_ms, diag.indicator_cache_ms,
        diag.db_latest_date_ms, diag.db_prices_ms, diag.analytics_ms, diag.guardrails_ms, diag.aggregator_ms,
        diag.direct_technical_used, diag.aggregator_called, diag.rag_called, diag.ensure_fresh_called,
        diag.refresh_if_needed_called, diag.external_api_called, diag.response_cache_hit, diag.indicator_cache_hit,
    )
    end_request_diagnostics()
    return response
