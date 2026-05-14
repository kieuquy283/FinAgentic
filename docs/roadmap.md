# Roadmap

Date: 2026-05-14

## Phase 1: Stabilize MVP
Goal:
- Keep demo runs repeatable and low-risk.

Scope:
- Harden startup/runbook scripts and docs.
- Expand fallback/error handling test coverage.
- Keep response contract stable.
- Freeze architecture and avoid feature expansion.

Success criteria:
- Consistent seed/test/start/build passes.
- 5 required queries work reliably across runs.

## Phase 2: Replace Mock Data With Real Ingestion
Goal:
- Move from deterministic mock files to trusted real data inputs.

Scope:
- Ingest official exchange/company disclosures and licensed vendor feeds.
- Add schema validation and normalization pipeline.
- Preserve DB-first facts boundary.

Success criteria:
- Automated ingestion produces queryable canonical DB tables.
- Data freshness and lineage tracked.

## Phase 3: Upgrade RAG To Qdrant Hybrid Retrieval
Goal:
- Improve qualitative evidence retrieval quality and traceability.

Scope:
- Add dense + sparse hybrid indexing in Qdrant.
- Add metadata filters, top-k fusion, rerank stage.
- Keep evidence snippet output mandatory.

Success criteria:
- Better recall/precision on news/report queries vs MVP baseline.

## Phase 4: Add Redis/Cache TTL
Goal:
- Improve latency and consistency for repeated requests.

Scope:
- Replace in-memory cache with Redis cache-aside.
- Add TTL policy by route type.
- Add cache key normalization and invalidation rules.

Success criteria:
- Improved P50/P95 latency and measurable cache hit rate.

## Phase 5: Add OpenAI-Compatible LLM Adapter
Goal:
- Enable controlled language synthesis where deterministic services already provide facts.

Scope:
- Add optional adapter for advisory phrasing and complex query fallback.
- Keep guardrails before final answer.
- Keep numeric facts sourced from DB/Python only.

Success criteria:
- No regression in factuality constraints.
- Improved answer naturalness without architecture violations.

## Phase 6: Add Observability And Evaluation
Goal:
- Make quality, reliability, and safety measurable.

Scope:
- Add structured logs, latency/error metrics, and traces.
- Add evaluation suite for routing, analytics correctness, retrieval quality, and guardrails.
- Add demo and regression dashboards.

Success criteria:
- Release gating based on objective quality and reliability metrics.
