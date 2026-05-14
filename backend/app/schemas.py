from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field


IntentType = Literal[
    "company_info",
    "market_data",
    "technical_analysis",
    "news_sentiment",
    "report_analysis",
    "investment_advisory",
    "forecast_outlook",
    "unknown",
]
RouteType = Literal[
    "company_direct",
    "market_data_direct",
    "analytics_direct",
    "rag_light",
    "advisory_llm",
    "planner_fallback",
    "unknown",
]
ConfidenceType = Literal["high", "medium", "low"]


class ChatRequest(BaseModel):
    query: str = Field(...)


class RouterResult(BaseModel):
    intent: IntentType
    tickers: list[str]
    date_range: Optional[str] = None
    indicators: list[str] = []
    window_size: Optional[int] = None
    need_news: bool = False
    need_reports: bool = False
    need_advice: bool = False
    confidence: ConfidenceType = "low"
    route: RouteType = "unknown"
    scores: dict = {}
    top_intent: IntentType = "unknown"
    second_intent: IntentType = "unknown"
    margin: float = 0.0
    time_context: Literal["past_range", "future_horizon", "unspecified"] = "unspecified"
    needs_planner: bool = False
    matched_keywords: list[str] = []


class EvidenceItem(BaseModel):
    source: str
    source_type: Literal["db", "analytics", "rag", "cache"]
    ticker: str
    date: str
    content: str


class GuardrailResult(BaseModel):
    passed: bool
    warnings: list[str] = []
    disclaimer: str


class CompanySnapshot(BaseModel):
    ticker: str
    company_name: str
    exchange: str
    sector: str
    description: str


class MarketSnapshot(BaseModel):
    ticker: str
    latest_close: float
    start_close: float
    return_3m_pct: float
    avg_volume_20d: float
    date_from: str
    date_to: str


class TechnicalSnapshot(BaseModel):
    ticker: str
    sma20: float
    rsi14: float
    return_pct: float
    source: str = "python_analytics"


class NewsSnapshot(BaseModel):
    ticker: str
    sentiment: Literal["positive", "negative", "neutral"]
    top_events: list[str]


class ReportSnapshot(BaseModel):
    ticker: str
    summary: str
    risks: list[str]


class AnalyticalContext(BaseModel):
    ticker: str
    company_snapshot: Optional[CompanySnapshot] = None
    market_snapshot: Optional[MarketSnapshot] = None
    technical_snapshot: Optional[TechnicalSnapshot] = None
    news_snapshot: Optional[NewsSnapshot] = None
    report_snapshot: Optional[ReportSnapshot] = None
    evidence: list[EvidenceItem] = []
    runtime_warnings: list[str] = []


class ChatResponse(BaseModel):
    query: str
    intent: IntentType
    route: RouteType
    answer: str
    evidence: list[EvidenceItem]
    confidence: ConfidenceType
    guardrails: GuardrailResult
    latency_ms: int
