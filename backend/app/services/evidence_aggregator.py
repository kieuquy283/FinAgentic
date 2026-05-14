from __future__ import annotations

from app.schemas import (
    AnalyticalContext,
    CompanySnapshot,
    MarketSnapshot,
    NewsSnapshot,
    ReportSnapshot,
    TechnicalSnapshot,
    EvidenceItem,
)
from app.services.analytics_service import AnalyticsService
from app.services.company_service import CompanyService
from app.services.market_data_service import MarketDataService
from app.services.rag_service import RagService


class EvidenceAggregator:
    def __init__(self):
        self.company_service = CompanyService()
        self.market_service = MarketDataService()
        self.analytics_service = AnalyticsService()
        self.rag_service = RagService()

    def build(self, ticker: str, query: str) -> AnalyticalContext:
        ctx = AnalyticalContext(ticker=ticker, evidence=[])
        if not ticker:
            return ctx

        company = self.company_service.get_company(ticker)
        if company:
            ctx.company_snapshot = CompanySnapshot(**dict(company))
            ctx.evidence.append(
                EvidenceItem(
                    source=str(company.get("source") or "sqlite_companies"),
                    source_type="db",
                    ticker=ticker,
                    date=str(company.get("fetched_at") or "N/A")[:10],
                    content=f"{company['company_name']} - {company['exchange']} - {company['sector']}",
                )
            )

        market = self.market_service.summarize_3m(ticker)
        rows = self.market_service.get_prices(ticker, 90)
        closes = [float(r["close"]) for r in rows]

        if market:
            ctx.market_snapshot = MarketSnapshot(**market)
            market_source = str(rows[-1].get("source") or "sqlite_prices") if rows else "sqlite_prices"
            ctx.evidence.append(
                EvidenceItem(
                    source=market_source,
                    source_type="db",
                    ticker=ticker,
                    date=market["date_to"],
                    content=f"close_start={market['start_close']}, close_latest={market['latest_close']}, return={market['return_3m_pct']}%",
                )
            )

        if len(closes) >= 20:
            ctx.technical_snapshot = TechnicalSnapshot(
                ticker=ticker,
                sma20=self.analytics_service.calculate_sma(closes, 20),
                rsi14=self.analytics_service.calculate_rsi(closes, 14),
                return_pct=self.analytics_service.calculate_return_pct(closes),
            )
            ctx.evidence.append(
                EvidenceItem(
                    source="python_analytics",
                    source_type="analytics",
                    ticker=ticker,
                    date=rows[-1]["date"] if rows else "2026-05-14",
                    content=f"SMA20={ctx.technical_snapshot.sma20}, RSI14={ctx.technical_snapshot.rsi14}",
                )
            )

        rag_items = self.rag_service.search(ticker, query, 5)
        ctx.evidence.extend(rag_items)

        if rag_items:
            sentiment = self.rag_service.score_sentiment(rag_items)
            ctx.news_snapshot = NewsSnapshot(ticker=ticker, sentiment=sentiment, top_events=[r.content for r in rag_items[:3]])
            report_texts = [r.content for r in rag_items if "report" in r.source.lower()]
            if report_texts:
                risks = [t for t in report_texts if "rui ro" in t.lower() or "ap luc" in t.lower()]
                ctx.report_snapshot = ReportSnapshot(
                    ticker=ticker,
                    summary=report_texts[0],
                    risks=risks[:3] or ["Chua xac dinh ro rui ro tu report"],
                )

        return ctx
