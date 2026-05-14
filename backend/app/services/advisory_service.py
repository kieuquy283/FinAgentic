from __future__ import annotations

from app.schemas import AnalyticalContext


class AdvisoryService:
    def synthesize(self, ctx: AnalyticalContext) -> str:
        if not ctx.company_snapshot or not ctx.market_snapshot or not ctx.technical_snapshot:
            return "Status: theo doi. Ly do: du lieu chua day du. Rui ro: thieu bang chung dinh luong."

        market = ctx.market_snapshot
        tech = ctx.technical_snapshot
        news = ctx.news_snapshot.sentiment if ctx.news_snapshot else "neutral"

        if tech.rsi14 > 70:
            status = "khong mua duoi"
        elif market.return_3m_pct > 0:
            status = "theo doi"
        else:
            status = "bao toan von"

        return (
            f"Status: {status}. "
            f"Dinh luong: return_3m={market.return_3m_pct}%, SMA20={tech.sma20}, RSI14={tech.rsi14}. "
            f"Dinh tinh: tin tuc nghieng {news}. "
            f"Rui ro: bien dong ngan han, thay doi sentiment tin tuc, rui ro nganh. "
            f"Confidence: medium."
        )
