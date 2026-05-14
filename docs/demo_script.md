# 5-minute Demo Script

## 1) Architecture Intro (45s)
- Hybrid Agentic RAG MVP for Vietnamese stock assistant.
- DB-first for structured facts, Python-first for indicators.
- RAG only for unstructured text (news/reports).
- Guardrails applied before final response.

## 2) Query 1 - Company Info (35s)
- Ask: "FPT niem yet o san nao?"
- Show direct route.
- Show evidence from `companies` table.

## 3) Query 2 - Market Data (40s)
- Ask: "Gia FPT 3 thang gan day the nao?"
- Show direct route + 90-row summary.
- Highlight start close, latest close, return.

## 4) Query 3 - Technical Analytics (45s)
- Ask: "Tinh RSI14 va SMA20 cua FPT."
- Show analytics route.
- Explain RSI14/SMA20 from deterministic Python service.

## 5) Query 4 - News Sentiment (40s)
- Ask: "Tin tuc gan day ve HPG la tich cuc hay tieu cuc?"
- Show rag route.
- Show top snippets and deterministic keyword sentiment.

## 6) Query 5 - Advisory (55s)
- Ask: "FPT co dang theo doi khong? Neu ly do va rui ro."
- Show advisory route uses AnalyticalContext only.
- Show quantitative + qualitative reasons and risks.

## 7) Limitations and Next Steps (40s)
- Mock deterministic data, not live market feed.
- Simple rule router and simple sentiment logic.
- Next: realtime ingestion, stronger retrieval, richer guardrails, better confidence scoring.
