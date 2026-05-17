from __future__ import annotations

import re
import time
from dataclasses import dataclass

from app.runtime_diagnostics import get_request_diagnostics
from app.schemas import AnalyticalContext, RouterResult


@dataclass
class ForecastOutlookResult:
    answer: str
    confidence: str


class ForecastOutlookService:
    def synthesize(self, ticker: str, query: str, horizon: str | None, router_result: RouterResult, ctx: AnalyticalContext) -> ForecastOutlookResult:
        t0 = time.perf_counter()
        stance = self._stance(ctx)
        m = ctx.market_snapshot
        t = ctx.technical_snapshot
        n = ctx.news_snapshot
        r = ctx.report_snapshot

        quant = []
        if m is not None:
            quant.append(f"return 3 thang gan nhat {m.return_3m_pct}% (tu {m.start_close} den {m.latest_close})")
            quant.append(f"thanh khoan TB20 ngay {m.avg_volume_20d}")
        if t is not None:
            quant.append(f"SMA20={t.sma20}, RSI14={t.rsi14}, return ky gan day={t.return_pct}%")
        if not quant:
            quant.append("chua co du du lieu dinh luong trong DB")

        qualitative = []
        if n is not None:
            qualitative.append(f"sentiment tin tuc: {n.sentiment}")
        else:
            qualitative.append("thieu bang chung tin tuc gan day")
        if r is not None:
            qualitative.append("co bang chung tu report")
        else:
            qualitative.append("chua co report gan day")

        risks = []
        if t is not None and t.rsi14 >= 70:
            risks.append("RSI cao, rui ro dieu chinh ngan han")
        if t is not None and t.rsi14 <= 35:
            risks.append("dong luc yeu, rui ro tiep tuc giam")
        if n is not None and n.sentiment == "negative":
            risks.append("dong tin tieu cuc co the gay ap luc gia")
        if not risks:
            risks.append("bien dong thi truong chung va tin tuc bat ngo")

        watch = [
            "duy tri gia tren SMA20",
            "bien dong RSI ve vung can bang 45-65",
            "chat luong tin tuc/ket qua kinh doanh cap nhat",
            "thanh khoan co duy tri tren muc trung binh hay khong",
        ]

        h = horizon or "1M"
        answer = (
            f"Trong khung {h} toi, {ticker} hien o trang thai {stance} dua tren du lieu hien co.\n"
            "Base scenario: dao dong theo xu huong hien tai, khong dua ra muc gia muc tieu cu the.\n"
            f"Positive scenario: dong luc ky thuat va dong tin duy tri tich cuc.\n"
            f"Negative scenario: ap luc dieu chinh neu xuat hien tin xau hoac suy yeu dong luc.\n"
            f"Ly do dinh luong: {'; '.join(quant)}.\n"
            f"Ly do dinh tinh: {'; '.join(qualitative)}.\n"
            f"Rui ro chinh: {'; '.join(risks)}.\n"
            f"Dau hieu can theo doi: {'; '.join(watch)}.\n"
            "Luu y: Day la danh gia kich ban dua tren du lieu lich su/gan day, khong phai du doan gia chinh xac."
        )

        conf = "medium" if m or t else "low"
        diag = get_request_diagnostics()
        if diag is not None:
            diag.forecast_outlook_ms = (time.perf_counter() - t0) * 1000
        return ForecastOutlookResult(answer=answer, confidence=conf)

    def _stance(self, ctx: AnalyticalContext) -> str:
        score = 0
        if ctx.market_snapshot is not None and ctx.market_snapshot.return_3m_pct > 0:
            score += 1
        if ctx.technical_snapshot is not None and ctx.technical_snapshot.rsi14 >= 55:
            score += 1
        if ctx.news_snapshot is not None and ctx.news_snapshot.sentiment == "positive":
            score += 1
        if ctx.news_snapshot is not None and ctx.news_snapshot.sentiment == "negative":
            score -= 1
        if score >= 2:
            return "positive"
        if score == 1:
            return "neutral_positive"
        if score == 0:
            return "neutral"
        if score == -1:
            return "cautious"
        return "negative"


def parse_forecast_horizon(query: str, date_range: str | None) -> str:
    q = query.lower()
    if date_range in {"1W", "1M", "3M"}:
        return date_range
    if any(x in q for x in ["1 tuan toi", "mot tuan toi", "tuan toi", "7 ngay toi"]):
        return "1W"
    if any(x in q for x in ["1 thang toi", "mot thang toi", "thang toi", "30 ngay toi"]):
        return "1M"
    if any(x in q for x in ["3 thang toi", "quy toi", "90 ngay toi"]):
        return "3M"
    return "1M"
