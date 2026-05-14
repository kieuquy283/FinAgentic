from __future__ import annotations

from app.schemas import AnalyticalContext

SYSTEM_PROMPT = (
    "You are a Vietnamese financial analysis assistant.\n"
    "You must synthesize only from the provided AnalyticalContext.\n"
    "You must not invent numbers, prices, news, ratios, or sources.\n"
    "You must not calculate indicators.\n"
    "If evidence is missing, say confidence is low.\n"
    "Always include risks.\n"
    "Never give personalized financial advice.\n"
    "Always include a disclaimer that the output is for reference only."
)


def build_user_prompt(ctx: AnalyticalContext) -> str:
    company = ctx.company_snapshot.model_dump() if ctx.company_snapshot else {}
    market = ctx.market_snapshot.model_dump() if ctx.market_snapshot else {}
    technical = ctx.technical_snapshot.model_dump() if ctx.technical_snapshot else {}
    news = ctx.news_snapshot.model_dump() if ctx.news_snapshot else {}
    report = ctx.report_snapshot.model_dump() if ctx.report_snapshot else {}

    evidence_lines = []
    for e in ctx.evidence:
        evidence_lines.append(
            f"- ticker={e.ticker} date={e.date} source={e.source} type={e.source_type} content={e.content}"
        )
    evidence_text = "\n".join(evidence_lines) if evidence_lines else "- none"

    return (
        "Synthesize a concise Vietnamese advisory summary using only this AnalyticalContext.\n"
        "Required sections: Status, Evidence summary, Risks, Confidence, Disclaimer.\n"
        "AnalyticalContext:\n"
        f"ticker: {ctx.ticker}\n"
        f"company_snapshot: {company}\n"
        f"market_snapshot: {market}\n"
        f"technical_snapshot: {technical}\n"
        f"news_snapshot: {news}\n"
        f"report_snapshot: {report}\n"
        f"evidence:\n{evidence_text}\n"
    )

