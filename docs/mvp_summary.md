# MVP Summary

Date: 2026-05-14

## Project goal
Build a 4-day MVP demo of a Hybrid Agentic RAG Vietnamese stock assistant that demonstrates:
- DB-first structured retrieval
- Python-first deterministic analytics
- RAG for unstructured text evidence
- Guardrails before final answer

## Architecture summary
- FastAPI backend with rule-based router (`direct`, `analytics`, `rag`, `advisory`).
- SQLite as structured data source (`companies`, `prices`, `news`, `reports`).
- Deterministic Python analytics for RSI14, SMA20, return.
- Deterministic keyword retrieval for news/report evidence.
- Evidence aggregation into typed `AnalyticalContext`.
- Advisory synthesis based on `AnalyticalContext`.
- Guardrails always append disclaimer and warnings.
- React + Vite frontend for demo interaction.

## Implemented components
- Rule-based query router with ticker/intent extraction.
- Company and market data services (DB-first).
- Analytics service (Python-first deterministic calculations).
- RAG service (local keyword retrieval + sentiment heuristic).
- Evidence aggregator + advisory synthesizer.
- Guardrails service for evidence/disclaimer checks.
- `/chat` orchestration with stable response contract and latency.
- In-memory cache for repeated queries.
- Frontend UI with sample buttons, loading/error states, evidence rendering.
- Tests for router, analytics, guardrails, and hardened chat API fallback cases.

## What is mocked
- Market/news/report dataset is deterministic demo seed data.
- Sentiment classification is keyword-based.
- Advisory confidence narrative is heuristic.
- No realtime exchange feed or external market API ingestion.

## What is production-ready in concept only
- Real ingestion pipelines (official exchange + vendor normalization).
- Hybrid vector+sparse retrieval in Qdrant with reranking.
- Redis cache-aside with TTL and invalidation.
- OpenAI-compatible LLM adapter and controlled synthesis fallback.
- Observability and evaluation pipelines (metrics, traces, quality dashboards).

## Limitations
- Rule-based router can miss wording variations.
- Retrieval and sentiment logic are simplistic.
- No personalized risk profile support.
- Cache has no TTL.
- Demo focuses on architecture pattern, not trading-grade data quality.

## Next roadmap
1. Stabilize MVP operations and demo runbook.
2. Replace mock data with real ingestion and validation.
3. Upgrade retrieval to Qdrant hybrid stack.
4. Add Redis TTL cache strategy.
5. Integrate OpenAI-compatible LLM adapter for synthesis.
6. Add observability + evaluation framework.
