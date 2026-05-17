from __future__ import annotations

import logging
import os
import re
import unicodedata
from dataclasses import dataclass
from math import sqrt

logger = logging.getLogger(__name__)

INTENTS = [
    "company_info",
    "market_data",
    "technical_analysis",
    "news_sentiment",
    "report_analysis",
    "investment_advisory",
    "forecast_outlook",
    "unknown",
]

KEYWORDS: dict[str, list[str]] = {
    "market_data": ["gia", "gia lich su", "du lieu gia", "ohlcv", "thong ke", "loi suat", "bien dong", "volume", "khoi luong", "3 thang gan day", "trong qua khu"],
    "technical_analysis": ["sma", "rsi", "macd", "bollinger", "ma20", "ma50", "trung binh dong", "chi bao ky thuat"],
    "forecast_outlook": [
        "du kien",
        "du bao",
        "du doan",
        "trien vong",
        "tinh hinh",
        "sap toi",
        "thang toi",
        "1 thang toi",
        "mot thang toi",
        "xu huong toi",
        "ky vong",
        "outlook",
        "forecast",
        "co tang khong",
        "co giam khong",
        "thoi gian toi",
        "3 thang toi",
        "quy toi",
        "30 ngay toi",
    ],
    "investment_advisory": ["co nen mua", "co dang mua", "co dang theo doi", "nam giu", "ban khong", "giai ngan", "khuyen nghi"],
    "news_sentiment": ["tin tuc", "sentiment", "tich cuc", "tieu cuc", "su kien", "anh huong"],
    "company_info": ["niem yet", "san nao", "nganh gi", "cong ty nao", "ho so doanh nghiep"],
    "report_analysis": ["bao cao", "phan tich bao cao", "report", "khuyen nghi tu bao cao", "rui ro tu bao cao"],
}

PROTOTYPES: dict[str, list[str]] = {
    "forecast_outlook": [
        "Du doan FPT co tang trong 3 thang toi khong?",
        "Trien vong FPT quy toi the nao?",
        "FPT sap toi co dang theo doi khong?",
        "Co phieu HPG co the tang trong thoi gian toi khong?",
        "Outlook cua VCB trong 3 thang toi?",
    ],
    "market_data": [
        "Thong ke du lieu gia lich su FPT trong 3 thang gan day",
        "Gia FPT 90 ngay gan nhat the nao?",
        "Loi suat FPT trong 3 thang qua",
        "Bien dong gia HPG gan day",
        "Du lieu OHLCV cua VNM trong qua khu",
    ],
    "technical_analysis": [
        "Tinh SMA20 cua FPT",
        "RSI14 cua HPG hien tai",
        "MACD cua VCB",
        "Chi bao ky thuat MA20 MA50 cua VNM",
        "Bollinger band cua FPT",
    ],
    "news_sentiment": [
        "Tin tuc HPG gan day tich cuc hay tieu cuc?",
        "Sentiment tin moi nhat ve FPT",
        "Su kien gan day anh huong VCB",
        "Danh gia tin tuc VNM",
        "Cam xuc thi truong ve HPG",
    ],
    "company_info": [
        "FPT niem yet o san nao?",
        "HPG thuoc nganh gi?",
        "Ho so doanh nghiep VCB",
        "VNM la cong ty nao?",
        "Thong tin niem yet cua FPT",
    ],
    "investment_advisory": [
        "FPT co nen mua khong?",
        "Toi co nen nam giu HPG?",
        "Co nen giai ngan VCB luc nay?",
        "FPT co dang theo doi khong?",
        "Khuyen nghi dau tu VNM",
    ],
    "report_analysis": [
        "Bao cao gan day ve FPT noi gi?",
        "Phan tich report cua HPG",
        "Rui ro tu bao cao VCB",
        "Khuyen nghi trong bao cao VNM",
        "Tong hop report FPT",
    ],
}

PAST_RANGE = ["gan day", "vua qua", "3 thang qua", "3 thang gan day", "90 ngay gan nhat", "lich su", "trong qua khu"]
FUTURE_HORIZON = [
    "sap toi",
    "thoi gian toi",
    "3 thang toi",
    "quy toi",
    "nam toi",
    "tuong lai",
    "thang toi",
    "1 thang toi",
    "mot thang toi",
    "30 ngay toi",
]
TICKERS = ["FPT", "HPG", "VCB", "VNM"]
INDICATORS = ["RSI", "SMA", "MACD", "BOLLINGER", "MA20", "MA50"]


def _norm(text: str) -> str:
    t = unicodedata.normalize("NFD", text)
    t = "".join(ch for ch in t if unicodedata.category(ch) != "Mn")
    t = t.replace("đ", "d").replace("Đ", "D")
    t = t.lower()
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _tokenize(text: str) -> set[str]:
    return set(_norm(text).split())


def _cosine_token_overlap(q: str, proto: str) -> float:
    a = _tokenize(q)
    b = _tokenize(proto)
    if not a or not b:
        return 0.0
    inter = len(a.intersection(b))
    return inter / (sqrt(len(a)) * sqrt(len(b)))


def _try_sentence_transformer_score(query: str, intent: str) -> float | None:
    if os.getenv("ENABLE_ST_ROUTER", "false").strip().lower() not in {"1", "true", "yes", "on"}:
        return None
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
        import numpy as np  # type: ignore
    except Exception:
        return None
    try:
        model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        texts = [query] + PROTOTYPES.get(intent, [])
        emb = model.encode(texts)
        qv = emb[0]
        sims = []
        for v in emb[1:]:
            denom = (np.linalg.norm(qv) * np.linalg.norm(v)) or 1.0
            sims.append(float(np.dot(qv, v) / denom))
        return max(sims) if sims else 0.0
    except Exception:
        return None


def _semantic_score(query: str, intent: str) -> float:
    st = _try_sentence_transformer_score(query, intent)
    if st is not None:
        return max(0.0, min(1.0, st))
    protos = PROTOTYPES.get(intent, [])
    if not protos:
        return 0.0
    return max(_cosine_token_overlap(query, p) for p in protos)


def _keyword_score(query: str, intent: str) -> tuple[float, list[str]]:
    q = _norm(query)
    kws = KEYWORDS.get(intent, [])
    matched = [k for k in kws if _norm(k) in q]
    if not kws:
        return 0.0, []
    return min(1.0, len(matched) / max(1, min(4, len(kws)))), matched


def _extract_tickers(query: str) -> list[str]:
    up = query.upper()
    return [t for t in TICKERS if t in up]


def _time_context(query: str) -> str:
    q = _norm(query)
    if any(_norm(k) in q for k in FUTURE_HORIZON):
        return "future_horizon"
    if any(_norm(k) in q for k in PAST_RANGE):
        return "past_range"
    return "unspecified"


def _entity_score(query: str, intent: str, tickers: list[str]) -> float:
    qn = _norm(query)
    score = 0.0
    has_ticker = len(tickers) > 0
    has_indicator = any(i.lower() in qn for i in [x.lower() for x in INDICATORS])
    has_news = any(x in qn for x in ["tin tuc", "sentiment", "bao cao", "report"])
    if has_ticker and intent in ["company_info", "market_data", "technical_analysis", "investment_advisory", "forecast_outlook", "news_sentiment", "report_analysis"]:
        score += 0.4
    if has_indicator and intent == "technical_analysis":
        score += 0.5
    if has_news and intent in ["news_sentiment", "report_analysis"]:
        score += 0.5
    return min(1.0, score)


def _time_score(intent: str, ctx: str) -> float:
    if ctx == "past_range" and intent in ["market_data", "technical_analysis"]:
        return 1.0
    if ctx == "future_horizon" and intent in ["forecast_outlook", "investment_advisory"]:
        return 1.0
    return 0.0


@dataclass
class RouterScoreResult:
    intent: str
    route: str
    confidence: float
    scores: dict
    top_intent: str
    second_intent: str
    margin: float
    time_context: str
    needs_planner: bool
    matched_keywords: list[str]
    tickers: list[str]
    indicators: list[str]
    date_range: str | None


@dataclass
class IndicatorSpec:
    indicator: str
    window: int | None


def parse_indicator_spec(query: str, indicators: list[str] | None = None, date_range: str | None = None) -> IndicatorSpec | None:
    qn = _norm(query)
    candidates = [x.upper() for x in (indicators or [])]

    if "return" in qn or "performance" in qn or "loi suat" in qn:
        if date_range == "3m" or "3 month" in qn or "3 thang" in qn:
            return IndicatorSpec(indicator="return", window=90)
        return IndicatorSpec(indicator="return", window=90)

    rsi_match = re.search(r"\brsi\s*(\d{1,3})?\b", qn, flags=re.IGNORECASE)
    if rsi_match or "RSI" in candidates:
        window = int(rsi_match.group(1)) if rsi_match and rsi_match.group(1) else 14
        return IndicatorSpec(indicator="rsi", window=window)

    sma_match = re.search(r"\bsma\s*(\d{1,3})?\b", qn, flags=re.IGNORECASE)
    if sma_match:
        window = int(sma_match.group(1)) if sma_match.group(1) else 20
        return IndicatorSpec(indicator="sma", window=window)
    if "MA20" in candidates:
        return IndicatorSpec(indicator="sma", window=20)
    if "MA50" in candidates:
        return IndicatorSpec(indicator="sma", window=50)
    if "SMA" in candidates:
        return IndicatorSpec(indicator="sma", window=20)

    # TODO: support macd, bollinger, volatility, drawdown in direct path
    return None


def _intent_to_route(intent: str) -> str:
    if intent == "company_info":
        return "company_direct"
    if intent == "market_data":
        return "market_data_direct"
    if intent == "technical_analysis":
        return "analytics_direct"
    if intent in ["news_sentiment", "report_analysis"]:
        return "rag_light"
    if intent in ["investment_advisory", "forecast_outlook"]:
        return "advisory_llm"
    return "planner_fallback"


def score_query(query: str) -> RouterScoreResult:
    tickers = _extract_tickers(query)
    qn = _norm(query)
    time_ctx = _time_context(query)
    scores: dict[str, dict] = {}
    all_matched: list[str] = []
    for intent in [i for i in INTENTS if i != "unknown"]:
        kw, matched = _keyword_score(query, intent)
        sem = _semantic_score(query, intent)
        ent = _entity_score(query, intent, tickers)
        ts = _time_score(intent, time_ctx)
        final = 0.45 * kw + 0.35 * sem + 0.15 * ent + 0.05 * ts
        scores[intent] = {
            "keyword_score": round(kw, 4),
            "semantic_score": round(sem, 4),
            "entity_score": round(ent, 4),
            "time_score": round(ts, 4),
            "final_score": round(final, 4),
            "matched_keywords": matched,
        }
        all_matched.extend(matched)

    # Strong forward-looking boost when ticker + forecast language appears.
    forecast_hit = any(_norm(k) in qn for k in KEYWORDS["forecast_outlook"])
    advisory_hit = any(_norm(k) in qn for k in KEYWORDS["investment_advisory"])
    if tickers and forecast_hit:
        scores["forecast_outlook"]["final_score"] = round(max(float(scores["forecast_outlook"]["final_score"]), 0.86), 4)
        scores["investment_advisory"]["final_score"] = round(max(float(scores["investment_advisory"]["final_score"]), 0.74), 4)
    elif tickers and advisory_hit and time_ctx == "future_horizon":
        scores["investment_advisory"]["final_score"] = round(max(float(scores["investment_advisory"]["final_score"]), 0.82), 4)

    ranked = sorted(scores.items(), key=lambda x: x[1]["final_score"], reverse=True)
    top_intent = ranked[0][0] if ranked else "unknown"
    top_score = float(ranked[0][1]["final_score"]) if ranked else 0.0
    second_intent = ranked[1][0] if len(ranked) > 1 else "unknown"
    second_score = float(ranked[1][1]["final_score"]) if len(ranked) > 1 else 0.0
    margin = max(0.0, top_score - second_score)

    # Domain gate: avoid forcing non-finance/noisy queries into finance intents.
    finance_signal = len(tickers) > 0 or len(all_matched) > 0
    if not finance_signal and top_score < 0.55:
        top_intent = "unknown"
        top_score = 0.0
        margin = 0.0
        second_intent = "unknown"

    route = "unknown" if top_intent == "unknown" else _intent_to_route(top_intent)
    safe_direct = route in {"company_direct", "market_data_direct", "analytics_direct", "rag_light", "advisory_llm"}
    if top_intent == "unknown":
        needs_planner = False
    elif top_score >= 0.80 and margin >= 0.15:
        needs_planner = False
    elif top_score >= 0.65 and safe_direct:
        needs_planner = False
    else:
        route = "planner_fallback"
        needs_planner = True

    indicators: list[str] = []
    for k in ["RSI", "SMA", "MACD", "BOLLINGER", "MA20", "MA50"]:
        if k.lower() in qn:
            indicators.append(k)
    date_range = None
    if any(x in qn for x in ["3 thang", "90 ngay", "3 thang gan day", "3 thang qua"]):
        date_range = "3m"
    elif any(x in qn for x in ["1 thang toi", "mot thang toi", "thang toi", "30 ngay toi"]):
        date_range = "1m_forward"

    logger.info(
        "router_score query=%s top_intent=%s margin=%.4f route=%s needs_planner=%s scores=%s",
        query,
        top_intent,
        margin,
        route,
        needs_planner,
        scores,
    )

    return RouterScoreResult(
        intent=top_intent,
        route=route,
        confidence=top_score,
        scores=scores,
        top_intent=top_intent,
        second_intent=second_intent,
        margin=margin,
        time_context=time_ctx,
        needs_planner=needs_planner,
        matched_keywords=sorted(set(all_matched)),
        tickers=tickers,
        indicators=indicators,
        date_range=date_range,
    )
