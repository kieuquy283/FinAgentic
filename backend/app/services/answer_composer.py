from __future__ import annotations

import re

from app.schemas import AnalyticalContext, CompanySnapshot, MarketSnapshot


class AnswerComposer:
    def compose_technical_answer(self, ticker: str, raw_answer: str, latest_price_date: str | None) -> str:
        m = re.search(r"(SMA|RSI)(\d+)\s*=\s*([0-9]+(?:\.[0-9]+)?)", raw_answer, flags=re.IGNORECASE)
        if m:
            indicator = m.group(1).upper()
            window = m.group(2)
            value = m.group(3)
            when = f" (dữ liệu đến {latest_price_date})" if latest_price_date and latest_price_date != "N/A" else ""
            if indicator == "SMA":
                return (
                    f"{indicator}{window} của {ticker} hiện khoảng {value}{when}. "
                    f"Đây là mức giá trung bình của {window} phiên gần nhất, thường dùng để quan sát xu hướng ngắn hạn."
                )
            return (
                f"{indicator}{window} của {ticker} hiện ở mức {value}{when}. "
                f"Chỉ báo này giúp nhận diện trạng thái động lực giá trong ngắn hạn."
            )
        if "return" in raw_answer.lower():
            return f"Hiệu suất gần đây của {ticker}: {raw_answer}"
        return raw_answer

    def compose_market_summary_answer(self, ticker: str, market: MarketSnapshot | None) -> str:
        if market is None:
            return f"Hiện chưa đủ dữ liệu để tóm tắt diễn biến giá của {ticker} trong giai đoạn bạn hỏi."
        trend = "tăng" if market.return_3m_pct >= 0 else "giảm"
        return (
            f"Trong 3 tháng gần đây, {ticker} có xu hướng {trend}. "
            f"Giá đóng cửa đã di chuyển từ {market.start_close} lên {market.latest_close}, tương đương {market.return_3m_pct}%. "
            f"Thanh khoản trung bình 20 phiên gần nhất khoảng {market.avg_volume_20d}. "
            "Đây là tóm tắt dữ liệu quá khứ, không phải dự báo giá tương lai."
        )

    def compose_forecast_outlook_answer(self, ticker: str, horizon: str, ctx: AnalyticalContext, draft: str) -> str:
        missing_qual = []
        if ctx.news_snapshot is None:
            missing_qual.append("tin tức")
        if ctx.report_snapshot is None:
            missing_qual.append("báo cáo")
        suffix = ""
        if missing_qual:
            suffix = f"\nPhần nhận định định tính còn hạn chế vì hệ thống chưa có đủ dữ liệu {', '.join(missing_qual)} mới."
        return f"{draft}{suffix}"

    def compose_company_info_answer(self, c: CompanySnapshot) -> str:
        return f"{c.ticker} đang niêm yết trên sàn {c.exchange}, thuộc nhóm {c.sector}."

    def compose_unknown_answer(self) -> str:
        return (
            "Mình chưa đủ thông tin để hiểu chính xác ý bạn trong câu hỏi này. "
            "Bạn có thể hỏi cụ thể hơn, ví dụ: giá FPT 3 tháng gần đây, SMA20 của FPT, "
            "tin tức gần đây về HPG, hoặc triển vọng FPT trong 1 tháng tới."
        )
