# Demo Hardening Report

Date: 2026-05-14

## Hardening changes made
- Backend `/chat` hardened for empty query input:
  - Returns safe `unknown` response with low confidence and clear guidance.
- Backend `/chat` hardened for missing ticker:
  - Returns clear error message for intent that needs ticker.
- Backend `/chat` hardened for DB/runtime failures:
  - Catches aggregator/data-access failures and returns safe user-facing fallback (no stack trace leakage).
- Backend fallback wording improved for unknown intent:
  - Concise guidance to use one of 5 demo queries.
- Kept response contract stable:
  - `confidence`, `guardrails.disclaimer`, and warnings always present.
- Frontend UI hardening:
  - Added loading state (`Loading...`, disabled buttons while request is in-flight).
  - Added explicit error state for request failures.
  - Made demo query area clearer (`Demo queries` label).
  - Improved evidence/warnings readability styling.
  - Always renders evidence section; shows placeholder when evidence is empty.
- Added backend API hardening tests:
  - Empty query safe fallback.
  - Unknown intent fallback.
  - Missing ticker clear error.
  - Simulated DB failure safe fallback.
- README demo-readiness updates:
  - Quick demo run section.
  - Exact demo query order.
  - Troubleshooting notes for common live-demo issues.

## Commands run
- `cd backend && python scripts/seed_data.py`
- `cd backend && pytest -q`
- Backend startup and checks:
  - `GET /health`
  - `POST /chat` for all 5 required demo queries
  - extra `POST /chat` checks for empty query and unknown query
- `cd frontend && npm run build`

## Results
- Seed script: passed, DB recreated successfully.
- Backend tests: passed (`15 passed`).
- Backend startup check: passed (`/health` => `ok`).
- 5 required demo queries: all passed end-to-end with expected routes/intents.
- Empty query: no crash, safe fallback response.
- Unknown query: no crash, safe fallback response.
- Frontend build: passed (`vite build` successful).

## Remaining risks
- Mock/demo data only; not realtime.
- Rule-based router may miss unexpected Vietnamese phrasing.
- Sentiment is lexicon-based and can be simplistic.
- Advisory narrative confidence text is heuristic.
- Shell/codepage can still show Vietnamese encoding artifacts in some terminal contexts.

## Final live-demo checklist
- [ ] Terminal 1: `cd backend`
- [ ] Run `python scripts/seed_data.py`
- [ ] Run `uvicorn app.main:app --reload`
- [ ] Verify backend with `http://127.0.0.1:8000/health`
- [ ] Terminal 2: `cd frontend`
- [ ] Run `npm install`
- [ ] Run `npm run dev`
- [ ] Open frontend URL shown by Vite
- [ ] Run demo queries in order:
  1. `FPT niem yet o san nao?`
  2. `Gia FPT 3 thang gan day the nao?`
  3. `Tinh RSI14 va SMA20 cua FPT.`
  4. `Tin tuc gan day ve HPG la tich cuc hay tieu cuc?`
  5. `FPT co dang theo doi khong? Neu ly do va rui ro.`
- [ ] Confirm each response shows: intent, route, confidence, warnings, disclaimer, evidence
- [ ] If DB error appears, rerun `python scripts/seed_data.py` and refresh
