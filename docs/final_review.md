# Final MVP Review

Date: 2026-05-14

## Overall status
- MVP is functionally complete and demo-runnable.
- All required validation commands passed after one documentation fix.

## Commands run
- `cd backend && pytest -q`
- `cd backend && python scripts/seed_data.py`
- Backend startup + health + manual 5-query `/chat` checks via PowerShell `Start-Process ... uvicorn ...` and `Invoke-RestMethod`
- `cd frontend && npm run build`

## Pass/Fail checklist
- [x] 1) DB-first, Python-first, RAG-for-text, Guardrails-before-final-answer
- [x] 2) All 5 required demo queries work end-to-end
- [x] 3) `/chat` response contract stable and consistent
- [x] 4) Numeric calculations deterministic and test-covered
- [x] 5) Advisory output uses `AnalyticalContext`/evidence path only
- [x] 6) No blocking runtime/import/path/env issues found in local run
- [x] 7) README setup instructions accurate (after fix below)
- [x] 8) No major architecture violation or over-engineering
- [x] 9) Live-demo weak points identified and documented

## Issues found
1. README architecture summary said “Chroma-based local retrieval,” but implementation currently uses deterministic keyword retrieval fallback over SQLite text.

## Fixes applied
1. Updated README line to match actual implementation:
   - `README.md`: replaced Chroma claim with deterministic keyword retrieval fallback description.

## Known limitations
- Data is mock/demo, not live exchange data.
- Router is rule-based and phrase-dependent.
- Sentiment is lexicon-based, not model-based.
- Advisory confidence text is largely heuristic (`Confidence: medium` in narrative while envelope confidence may be `high` from routing/guardrails).
- Cache has no TTL and appends cache evidence on hits.
- Vietnamese text in some docs appears encoding-garbled in this shell/codepage environment.

## Demo readiness verdict
- Verdict: **READY for MVP demo**.
- Risk level: **Low to Medium** (mainly language/heuristic quality risk, not runtime stability risk).
