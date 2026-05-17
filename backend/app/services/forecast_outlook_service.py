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
            quant.append(f"return 3 tháng gần nhất {m.return_3m_pct}% (từ {m.start_close} đến {m.latest_close})")
            quant.append(f"thanh khoản TB20 ngày {m.avg_volume_20d}")
        if t is not None:
            quant.append(f"SMA20={t.sma20}, RSI14={t.rsi14}, return kỳ gần đây={t.return_pct}%")
        if not quant:
            quant.append("chưa có đủ dữ liệu định lượng trong DB")

        qualitative = []
        if n is not None:
            qualitative.append(f"sentiment tin tức: {n.sentiment}")
        else:
            qualitative.append("thiếu bằng chứng tin tức gần đây")
        if r is not None:
            qualitative.append("có bằng chứng từ report")
        else:
            qualitative.append("chưa có report gần đây")

        risks = []
        if t is not None and t.rsi14 >= 70:
            risks.append("RSI cao, rủi ro điều chỉnh ngắn hạn")
        if t is not None and t.rsi14 <= 35:
            risks.append("động lực yếu, rủi ro tiếp tục giảm")
        if n is not None and n.sentiment == "negative":
            risks.append("dòng tin tiêu cực có thể gây áp lực giá")
        if not risks:
            risks.append("biến động thị trường chung và tin tức bất ngờ")

        watch = [
            "duy trì giá trên SMA20",
            "biến động RSI về vùng cân bằng 45-65",
            "chất lượng tin tức/kết quả kinh doanh cập nhật",
            "thanh khoản có duy trì trên mức trung bình hay không",
        ]

        h = horizon or "1M"
        answer = (
            f"Trong khung {h} tới, {ticker} hiện ở trạng thái {stance} dựa trên dữ liệu hiện có.\n"
            "Base scenario: dao động theo xu hướng hiện tại, không đưa ra mức giá mục tiêu cụ thể.\n"
            "Positive scenario: động lực kỹ thuật và dòng tin duy trì tích cực.\n"
            "Negative scenario: áp lực điều chỉnh nếu xuất hiện tin xấu hoặc suy yếu động lực.\n"
            f"Lý do định lượng: {'; '.join(quant)}.\n"
            f"Lý do định tính: {'; '.join(qualitative)}.\n"
            f"Rủi ro chính: {'; '.join(risks)}.\n"
            f"Dấu hiệu cần theo dõi: {'; '.join(watch)}.\n"
            "Lưu ý: Đây là đánh giá kịch bản dựa trên dữ liệu lịch sử/gần đây, không phải dự đoán giá chính xác."
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
