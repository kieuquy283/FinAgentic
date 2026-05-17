from __future__ import annotations

import os
import time
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

from app.cache import get_cache, normalize_query, set_cache
from app.router import route_query
from app import scheduler as scheduler_mod
from app.schemas import ChatRequest, ChatResponse, EvidenceItem
from app.services.advisory_service import AdvisoryService
from app.services.direct_technical_service import DirectTechnicalService
from app.services.evidence_aggregator import EvidenceAggregator
from app.services.guardrails import DISCLAIMER, apply_guardrails

logger = logging.getLogger(__name__)


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
    route_ms = 0.0
    cache_ms = 0.0
    direct_technical_ms = 0.0
    guardrails_ms = 0.0
    aggregator_ms = 0.0
    query = req.query.strip()
    if not query:
        return _safe_response(
            query=req.query,
            intent="unknown",
            route="unknown",
            answer="Vui long nhap cau hoi co ticker, vi du: FPT niem yet o san nao?",
            warnings=["Cau hoi rong.", "Du lieu dang o che do demo/mock."],
            latency_ms=int((time.perf_counter() - start) * 1000),
        )

    key = normalize_query(query)
    t_cache = time.perf_counter()
    cached = get_cache(key)
    cache_ms = (time.perf_counter() - t_cache) * 1000
    if cached is not None:
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
        return ChatResponse(
            query=cached.query,
            intent=cached.intent,
            route=cached.route,
            answer=cached.answer,
            evidence=ev,
            confidence=cached.confidence,
            guardrails=cached.guardrails,
            latency_ms=int((time.perf_counter() - start) * 1000),
        )

    t_route = time.perf_counter()
    router_result = route_query(query)
    route_ms = (time.perf_counter() - t_route) * 1000
    ticker = router_result.tickers[0] if router_result.tickers else ""

    if router_result.intent != "unknown" and not ticker:
        return _safe_response(
            query=query,
            intent=router_result.intent,
            route=router_result.route,
            answer="Khong tim thay ticker hop le. Vui long dung ma co phieu nhu FPT, HPG, VCB, VNM.",
            warnings=["Thieu ticker trong cau hoi.", "Du lieu dang o che do demo/mock."],
            latency_ms=int((time.perf_counter() - start) * 1000),
        )

    direct_service = DirectTechnicalService()
    if direct_service.can_handle(router_result, query):
        t_direct = time.perf_counter()
        direct_result = direct_service.handle(query=query, router_result=router_result)
        direct_technical_ms = (time.perf_counter() - t_direct) * 1000

        t_guard = time.perf_counter()
        guard = apply_guardrails(
            intent=router_result.intent,
            answer=direct_result.answer,
            evidence=direct_result.evidence,
            has_numeric=True,
            demo_fallback=False,
            runtime_warnings=direct_result.warnings,
        )
        guardrails_ms = (time.perf_counter() - t_guard) * 1000
        conf = router_result.confidence if guard.passed else "low"
        response = ChatResponse(
            query=req.query,
            intent=router_result.intent,
            route=router_result.route,
            answer=f"{direct_result.answer}\n{guard.disclaimer}",
            evidence=direct_result.evidence,
            confidence=conf,
            guardrails=guard,
            latency_ms=int((time.perf_counter() - start) * 1000),
        )
        set_cache(key, response)
        logger.info(
            "chat_latency total_ms=%.2f route_ms=%.2f cache_ms=%.2f direct_technical_ms=%.2f db_ms=%.2f analytics_ms=%.2f guardrails_ms=%.2f aggregator_ms=%.2f",
            (time.perf_counter() - start) * 1000,
            route_ms,
            cache_ms + direct_result.cache_ms,
            direct_technical_ms,
            direct_result.db_ms,
            direct_result.analytics_ms,
            guardrails_ms,
            aggregator_ms,
        )
        return response

    aggregator = EvidenceAggregator()
    advisory = AdvisoryService()
    try:
        t_agg = time.perf_counter()
        ctx = aggregator.build(ticker=ticker, query=query)
        aggregator_ms = (time.perf_counter() - t_agg) * 1000
    except Exception:
        return _safe_response(
            query=query,
            intent=router_result.intent,
            route=router_result.route,
            answer="He thong du lieu chua san sang. Vui long chay lai script seed du lieu backend.",
            warnings=["Khong the truy cap CSDL du lieu demo.", "Du lieu dang o che do demo/mock."],
            latency_ms=int((time.perf_counter() - start) * 1000),
        )

    if router_result.intent == "company_info" and ctx.company_snapshot:
        answer = f"{ctx.company_snapshot.ticker} niem yet tren san {ctx.company_snapshot.exchange}."
    elif router_result.intent == "market_data" and ctx.market_snapshot:
        m = ctx.market_snapshot
        trend = "tang" if m.return_3m_pct >= 0 else "giam"
        answer = f"Gia {ticker} 3 thang {trend} {abs(m.return_3m_pct)}%, tu {m.start_close} den {m.latest_close}."
    elif router_result.intent == "technical_analysis" and ctx.technical_snapshot:
        t = ctx.technical_snapshot
        answer = f"{ticker}: RSI14={t.rsi14}, SMA20={t.sma20}, Return={t.return_pct}%."
    elif router_result.intent == "news_sentiment" and ctx.news_snapshot:
        answer = f"Tin tuc gan day ve {ticker} nghieng ve {ctx.news_snapshot.sentiment}."
    elif router_result.intent == "investment_advisory":
        answer = advisory.synthesize(ctx)
    else:
        answer = "Chua hieu ro cau hoi. Vui long thu 1 trong 5 cau hoi demo."

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
    guardrails_ms = (time.perf_counter() - t_guard) * 1000
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
    logger.info(
        "chat_latency total_ms=%.2f route_ms=%.2f cache_ms=%.2f direct_technical_ms=%.2f db_ms=%.2f analytics_ms=%.2f guardrails_ms=%.2f aggregator_ms=%.2f",
        (time.perf_counter() - start) * 1000,
        route_ms,
        cache_ms,
        direct_technical_ms,
        0.0,
        0.0,
        guardrails_ms,
        aggregator_ms,
    )
    return response
