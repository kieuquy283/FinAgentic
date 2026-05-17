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
            when = f" (du lieu den {latest_price_date})" if latest_price_date and latest_price_date != "N/A" else ""
            if indicator == "SMA":
                return (
                    f"{indicator}{window} cua {ticker} hien khoang {value}{when}. "
                    f"Day la muc gia trung binh cua {window} phien gan nhat, thuong dung de quan sat xu huong ngan han."
                )
            return (
                f"{indicator}{window} cua {ticker} hien o muc {value}{when}. "
                f"Chi bao nay giup nhan dien trang thai dong luc gia trong ngan han."
            )
        if "return" in raw_answer.lower():
            return f"Hieu suat gan day cua {ticker}: {raw_answer}"
        return raw_answer

    def compose_market_summary_answer(self, ticker: str, market: MarketSnapshot | None) -> str:
        if market is None:
            return f"Hien chua du du lieu de tom tat dien bien gia cua {ticker} trong giai doan ban hoi."
        trend = "tang" if market.return_3m_pct >= 0 else "giam"
        return (
            f"Trong 3 thang gan day, {ticker} co xu huong {trend}. "
            f"Gia dong cua da di chuyen tu {market.start_close} len {market.latest_close}, tuong duong {market.return_3m_pct}%. "
            f"Thanh khoan trung binh 20 phien gan nhat khoang {market.avg_volume_20d}. "
            "Day la tom tat du lieu qua khu, khong phai du bao gia tuong lai."
        )

    def compose_forecast_outlook_answer(self, ticker: str, horizon: str, ctx: AnalyticalContext, draft: str) -> str:
        missing_qual = []
        if ctx.news_snapshot is None:
            missing_qual.append("tin tuc")
        if ctx.report_snapshot is None:
            missing_qual.append("bao cao")
        suffix = ""
        if missing_qual:
            suffix = f"\nPhan nhan dinh dinh tinh con han che vi he thong chua co du du lieu {', '.join(missing_qual)} moi."
        return f"{draft}{suffix}"

    def compose_company_info_answer(self, c: CompanySnapshot) -> str:
        return f"{c.ticker} dang niem yet tren san {c.exchange}, thuoc nhom {c.sector}."

    def compose_unknown_answer(self) -> str:
        return (
            "Minh chua du thong tin de hieu chinh xac y ban trong cau hoi nay. "
            "Ban co the hoi cu the hon, vi du: gia FPT 3 thang gan day, SMA20 cua FPT, "
            "tin tuc gan day ve HPG, hoac danh gia trien vong FPT trong 1 thang toi."
        )
