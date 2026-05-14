from __future__ import annotations

import re
from typing import Optional
from app.schemas import RouterResult

TICKERS = ["FPT", "HPG", "VCB", "VNM"]


def _extract_tickers(query: str) -> list[str]:
    upper = query.upper()
    return [t for t in TICKERS if t in upper]


def route_query(query: str) -> RouterResult:
    q = query.lower()
    tickers = _extract_tickers(query)

    intent = "unknown"
    route = "unknown"
    indicators: list[str] = []
    window_size: Optional[int] = None
    date_range: Optional[str] = None

    if any(k in q for k in ["niem yet", "niêm yết", "san", "sàn", "exchange"]):
        intent, route = "company_info", "direct"
    elif any(k in q for k in ["gia", "giá", "3 thang", "3 tháng", "ohlcv", "xu huong", "xu hướng"]):
        intent, route, date_range = "market_data", "direct", "3m"
    elif any(k in q for k in ["rsi", "sma", "chi bao", "chỉ báo", "return"]):
        intent, route = "technical_analysis", "analytics"
        if "rsi" in q:
            indicators.append("RSI")
            window_size = 14
        if "sma" in q:
            indicators.append("SMA")
            window_size = 20 if "20" in q else window_size
    elif any(k in q for k in ["tin tuc", "tin tức", "tich cuc", "tích cực", "tieu cuc", "tiêu cực", "sentiment"]):
        intent, route = "news_sentiment", "rag"
    elif any(k in q for k in ["dang theo doi", "đáng theo dõi", "nen mua", "nên mua", "nam giu", "nắm giữ", "rui ro", "rủi ro"]):
        intent, route = "investment_advisory", "advisory"

    confidence = "high" if intent != "unknown" and tickers else ("medium" if intent != "unknown" else "low")

    return RouterResult(
        intent=intent,
        tickers=tickers,
        date_range=date_range,
        indicators=indicators,
        window_size=window_size,
        need_news=intent in ["news_sentiment", "investment_advisory"],
        need_reports=intent in ["news_sentiment", "investment_advisory"],
        need_advice=intent == "investment_advisory",
        confidence=confidence,
        route=route,
    )
