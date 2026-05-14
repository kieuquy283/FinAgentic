from __future__ import annotations

from sqlalchemy import text
from app.db import get_engine
from app.schemas import EvidenceItem


class RagService:
    def search(self, ticker: str, query: str, top_k: int = 5) -> list[EvidenceItem]:
        if not ticker:
            return []
        engine = get_engine()
        q = query.lower()

        with engine.connect() as conn:
            news_rows = conn.execute(
                text(
                    """
                    SELECT date, source, COALESCE(content, TRIM(COALESCE(title, '') || ' ' || COALESCE(snippet, ''))) AS content
                    FROM news
                    WHERE ticker = :ticker
                    ORDER BY date DESC
                    LIMIT 10
                    """
                ),
                {"ticker": ticker},
            ).mappings().all()
            report_rows = conn.execute(
                text("SELECT date, source, content FROM reports WHERE ticker = :ticker ORDER BY date DESC LIMIT 10"),
                {"ticker": ticker},
            ).mappings().all()

        rows = list(news_rows) + list(report_rows)
        scored = []
        for r in rows:
            content = r["content"].lower()
            score = 0
            for token in q.split():
                if token in content:
                    score += 1
            scored.append((score, r))

        scored.sort(key=lambda x: x[0], reverse=True)
        out: list[EvidenceItem] = []
        for _, r in scored[:top_k]:
            out.append(EvidenceItem(source=r["source"], source_type="rag", ticker=ticker, date=r["date"], content=r["content"]))
        return out

    def score_sentiment(self, snippets: list[EvidenceItem]) -> str:
        pos_keys = ["tang truong", "loi nhuan", "tich cuc", "vuot ky vong"]
        neg_keys = ["giam", "lo", "tieu cuc", "ap luc", "rui ro", "dieu tra"]
        score = 0
        for s in snippets:
            c = s.content.lower()
            score += sum(1 for k in pos_keys if k in c)
            score -= sum(1 for k in neg_keys if k in c)
        if score > 0:
            return "positive"
        if score < 0:
            return "negative"
        return "neutral"
