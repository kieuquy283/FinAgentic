# CODEX_TASKS.md

# Hybrid Agentic RAG Finance Demo - Codex Task Board

## 0. Mission

Build a 4-day MVP demo of a Hybrid Agentic RAG architecture for a Vietnamese stock investment assistant.

The system must demonstrate:

1. DB-first retrieval for structured financial/company data.
2. Python-first analytics for numeric calculations.
3. Hybrid RAG for news/report text.
4. Rule-based router with fallback-ready design.
5. Evidence aggregation into a typed `AnalyticalContext`.
6. Advisory synthesis based only on evidence.
7. Guardrails before final response.
8. Minimal frontend chat UI.
9. Tests for critical deterministic components.

This is a demo, not a production trading system.

---

## 1. Core Rule for Codex

Codex must work task-by-task.

For every task:

1. Read the task.
2. Implement only that task.
3. Run relevant tests/checks.
4. Fix errors.
5. Update the task status.
6. Add notes about what changed.
7. Move to the next task only after the current task passes its Definition of Done.

Do not skip tasks.
Do not over-engineer.
Do not introduce unnecessary frameworks.
Do not replace deterministic services with LLM logic.

---

## 2. Status Legend

Use these statuses:

```txt
[ ] Not started
[/] In progress
[x] Done
[!] Blocked
```

When completing a task, change:

```txt
[ ] Task name
```

to:

```txt
[x] Task name
```

and add a short completion note.

---

## 3. Tech Stack

Recommended demo stack:

```txt
Backend: FastAPI
Frontend: React + Vite
Structured DB: SQLite
Vector DB: Chroma local
Analytics: pandas / numpy
Testing: pytest
Cache: in-memory dict first
LLM: mock synthesizer first, OpenAI-compatible adapter optional
```

Avoid production-only infrastructure for this MVP:

```txt
Do not add ClickHouse yet.
Do not add Kafka yet.
Do not add Kubernetes.
Do not add complex multi-agent frameworks.
Do not require paid APIs for the base demo.
```

---

## 4. Target Repository Structure

Create or maintain this structure:

```txt
finance-agentic-rag-demo/
  backend/
    app/
      __init__.py
      main.py
      router.py
      schemas.py
      db.py
      cache.py
      services/
        __init__.py
        company_service.py
        market_data_service.py
        analytics_service.py
        rag_service.py
        evidence_aggregator.py
        advisory_service.py
        guardrails.py
    scripts/
      seed_data.py
    tests/
      test_router.py
      test_analytics.py
      test_guardrails.py
    requirements.txt
  frontend/
    package.json
    index.html
    src/
      App.jsx
      main.jsx
      api.js
  data/
    companies.json
    prices.csv
    news.json
    reports.json
  docs/
    architecture.md
    demo_script.md
  README.md
  CODEX_TASKS.md
```

---

## 5. Demo Queries That Must Work

The system must support these exact Vietnamese demo queries:

```txt
FPT niêm yết ở sàn nào?
Giá FPT 3 tháng gần đây thế nào?
Tính RSI14 và SMA20 của FPT.
Tin tức gần đây về HPG là tích cực hay tiêu cực?
FPT có đáng theo dõi không? Nêu lý do và rủi ro.
```

---

## 6. Response Contract

The `/chat` endpoint should return this structure:

```json
{
  "query": "string",
  "intent": "string",
  "route": "direct | analytics | rag | advisory | unknown",
  "answer": "string",
  "evidence": [
    {
      "source": "string",
      "source_type": "db | analytics | rag | cache",
      "ticker": "string",
      "date": "string",
      "content": "string"
    }
  ],
  "confidence": "high | medium | low",
  "guardrails": {
    "passed": true,
    "warnings": ["string"],
    "disclaimer": "string"
  },
  "latency_ms": 0
}
```

---

## 7. Definition of Done

A task is done only when:

1. Code is implemented.
2. Relevant tests pass.
3. App still starts.
4. No obvious runtime errors.
5. README or docs are updated if behavior changed.
6. Task status is updated in this file.

For backend tasks, run:

```bash
cd backend
pytest
uvicorn app.main:app --reload
```

For frontend tasks, run:

```bash
cd frontend
npm install
npm run dev
```

If a command is not available, document the issue in the task note.

---

# TASK BOARD

---

## Phase 1 - Project Skeleton

### T001 - Create repository skeleton

Status: [x]

Goal:
Create the monorepo structure for backend, frontend, data, docs, and tests.

Implementation notes:
- Create required directories.
- Add empty `__init__.py` files.
- Add minimal README.
- Add this task file as `CODEX_TASKS.md`.

Definition of Done:
- Folder structure exists.
- README exists.
- Backend package imports do not fail.

Completion notes:
- Implemented monorepo skeleton with backend/frontend/data/docs and package init files.
- Checks: backend imports resolved in pytest run.
- Limitation: none.

---

### T002 - Create backend FastAPI app

Status: [x]

Goal:
Create a minimal FastAPI backend.

Required files:
- `backend/app/main.py`
- `backend/requirements.txt`

Required endpoints:
- `GET /health`
- `POST /chat`

Implementation notes:
- `/health` returns `{ "status": "ok" }`.
- `/chat` can return a placeholder response initially.
- Add CORS middleware for frontend.

Definition of Done:
- `uvicorn app.main:app --reload` starts.
- `GET /health` works.
- No import errors.

Completion notes:
- Implemented FastAPI app with CORS, GET /health, POST /chat.
- Checks: uvicorn startup + /health passed.
- Limitation: none.

---

### T003 - Add backend schemas

Status: [x]

Goal:
Create typed Pydantic schemas for router output, evidence, guardrails, analytical context, and chat response.

Required file:
- `backend/app/schemas.py`

Required models:
- `RouterResult`
- `EvidenceItem`
- `GuardrailResult`
- `CompanySnapshot`
- `MarketSnapshot`
- `TechnicalSnapshot`
- `NewsSnapshot`
- `ReportSnapshot`
- `AnalyticalContext`
- `ChatResponse`

Definition of Done:
- Schemas import successfully.
- `/chat` uses `ChatResponse`.

Completion notes:
- Added required typed schemas including RouterResult, EvidenceItem, GuardrailResult, AnalyticalContext, ChatResponse.
- Checks: schema imports validated by tests and app startup.
- Limitation: ASCII Vietnamese for environment stability.

---

## Phase 2 - Seed Data and Structured DB

### T004 - Create seed data

Status: [x]

Goal:
Create deterministic demo data for Vietnamese stocks.

Required files:
- `data/companies.json`
- `data/prices.csv`
- `data/news.json`
- `data/reports.json`

Minimum tickers:
- FPT
- HPG
- VCB
- VNM

Data requirements:
- Company name
- Exchange
- Sector
- Short description
- At least 90 trading days of OHLCV-like data for FPT and HPG
- 5-10 news items
- 2-4 report snippets

Definition of Done:
- Data files exist.
- JSON files are valid.
- CSV is readable by pandas.

Completion notes:
- Created deterministic seed files companies/prices/news/reports in data/.
- Checks: JSON parse + CSV read via seed flow.
- Limitation: mock demo data only.

---

### T005 - Create SQLite DB and seed script

Status: [x]

Goal:
Load seed data into SQLite.

Required files:
- `backend/app/db.py`
- `backend/scripts/seed_data.py`

Required tables:
- `companies`
- `prices`
- `news`
- `reports`

Definition of Done:
- Running `python scripts/seed_data.py` creates SQLite DB.
- Data can be queried from the DB.
- Seed script is idempotent.

Completion notes:
- Added SQLite DB module and idempotent seed script loading companies/prices/news/reports.
- Checks: python scripts/seed_data.py passed.
- Limitation: runtime DB path uses backend/data for sandbox write stability.

---

## Phase 3 - Rule-based Router

### T006 - Implement rule-based router

Status: [x]

Goal:
Create a deterministic router for simple Vietnamese finance queries.

Required file:
- `backend/app/router.py`

Router must extract:
- intent
- tickers
- date_range
- indicators
- window_size
- need_news
- need_reports
- need_advice
- confidence
- route

Supported intents:
- `company_info`
- `market_data`
- `technical_analysis`
- `news_sentiment`
- `investment_advisory`
- `unknown`

Routing rules:
- Company listing/exchange questions -> direct
- Price/OHLCV questions -> direct
- SMA/RSI questions -> analytics
- News/sentiment questions -> rag
- “có đáng theo dõi/mua/nắm giữ” -> advisory

Definition of Done:
- Router handles all 5 demo queries.
- Confidence is deterministic.
- No LLM is used.

Completion notes:
- Implemented deterministic Vietnamese rule-based router with intent/route/extractions/confidence fields.
- Checks: covered by router tests + manual 5-query run.
- Limitation: pattern-based rules only.

---

### T007 - Add router tests

Status: [x]

Goal:
Test router behavior.

Required file:
- `backend/tests/test_router.py`

Test all 5 demo queries.

Definition of Done:
- `pytest backend/tests/test_router.py` passes.
- Each query maps to expected intent and route.

Completion notes:
- Added router tests for all 5 required demo queries.
- Checks: pytest backend/tests/test_router.py passed.
- Limitation: no fuzzy-language variants beyond rule set.

---

## Phase 4 - Direct Structured Services

### T008 - Implement company service

Status: [x]

Goal:
Create DB-first company lookup.

Required file:
- `backend/app/services/company_service.py`

Required behavior:
- Lookup ticker.
- Return company profile.
- Include source metadata.

Definition of Done:
- FPT exchange lookup works.
- Missing ticker returns clear error or low-confidence result.

Completion notes:
- Implemented DB-first company service lookup with structured fields.
- Checks: FPT exchange returned via /chat and evidence.
- Limitation: unknown ticker returns empty snapshot (handled upstream).

---

### T009 - Implement market data service

Status: [x]

Goal:
Create DB-first market data retrieval.

Required file:
- `backend/app/services/market_data_service.py`

Required behavior:
- Get OHLCV data by ticker.
- Support simple range such as 3 months / last 90 rows.
- Return summary: latest close, start close, return percent, average volume.

Definition of Done:
- FPT 3-month price query returns structured data.
- Evidence includes source and date range.

Completion notes:
- Implemented DB-first market data retrieval and 3M summary (start/latest/return/avg volume).
- Checks: market query passed with evidence and expected route.
- Limitation: fixed 90-row window for MVP.

---

## Phase 5 - Python Analytics

### T010 - Implement analytics service

Status: [x]

Goal:
Compute deterministic technical indicators in Python.

Required file:
- `backend/app/services/analytics_service.py`

Required indicators:
- SMA20
- SMA50 optional
- RSI14
- Return percent

Rules:
- LLM must not calculate numbers.
- Use pandas/numpy.
- Handle insufficient data gracefully.

Definition of Done:
- `calculate_sma(prices, window=20)` works.
- `calculate_rsi(prices, window=14)` works.
- FPT query returns SMA20 and RSI14.

Completion notes:
- Implemented deterministic numpy analytics (SMA, RSI, return) with insufficient-data errors.
- Checks: analytics tests passed and /chat analytics query works.
- Limitation: RSI uses simple average gains/losses.

---

### T011 - Add analytics tests

Status: [x]

Goal:
Test numeric calculations.

Required file:
- `backend/tests/test_analytics.py`

Test:
- SMA on known series.
- RSI returns a number between 0 and 100.
- Insufficient data behavior.

Definition of Done:
- Tests pass.
- No LLM dependency.

Completion notes:
- Added analytics tests for known SMA, RSI bounds, insufficient data behavior.
- Checks: pytest backend/tests/test_analytics.py passed.
- Limitation: no advanced indicator variants.

---

## Phase 6 - RAG Demo

### T012 - Implement simple RAG service

Status: [x]

Goal:
Implement local retrieval over news/report snippets.

Required file:
- `backend/app/services/rag_service.py`

Preferred:
- Use Chroma if easy.
- If Chroma setup causes delay, use simple BM25/keyword retrieval as fallback and document it.

Required behavior:
- Search by ticker and query.
- Return top evidence snippets.
- Include source, date, source type.

Definition of Done:
- HPG news sentiment query retrieves relevant news.
- Report snippets can be searched.

Completion notes:
- Implemented simple local RAG fallback using keyword retrieval over SQLite news/reports.
- Checks: HPG news query retrieved evidence and routed to rag.
- Limitation: Chroma skipped due native build constraint in environment.

---

### T013 - Add sentiment scoring

Status: [x]

Goal:
Add simple deterministic sentiment scoring for news snippets.

Implementation:
- Keyword-based positive/negative/neutral scoring is enough for demo.
- Positive examples: tăng trưởng, lợi nhuận, tích cực, vượt kỳ vọng
- Negative examples: giảm, lỗ, tiêu cực, áp lực, rủi ro, điều tra

Definition of Done:
- HPG news query returns positive/negative/neutral summary.
- Evidence is included.

Completion notes:
- Added deterministic keyword-based sentiment scoring positive/negative/neutral.
- Checks: HPG sentiment query returns classified summary with evidence.
- Limitation: lexicon-based scoring only.

---

## Phase 7 - Evidence and Advisory

### T014 - Implement evidence aggregator

Status: [x]

Goal:
Build a typed `AnalyticalContext` from service outputs.

Required file:
- `backend/app/services/evidence_aggregator.py`

Required behavior:
- Combine company, market, technical, news, and report snapshots.
- Keep evidence references.
- Do not generate unsupported claims.

Definition of Done:
- Advisory query for FPT creates an `AnalyticalContext`.
- Context has structured snapshots.

Completion notes:
- Implemented evidence aggregator building typed AnalyticalContext snapshots + evidence list.
- Checks: advisory query builds context used by synthesizer.
- Limitation: lightweight snapshot model for MVP.

---

### T015 - Implement advisory synthesizer

Status: [x]

Goal:
Generate a simple advisory-style answer from `AnalyticalContext`.

Required file:
- `backend/app/services/advisory_service.py`

Rules:
- Use evidence only.
- Do not claim personalized advice.
- Include:
  - status: theo dõi / nắm giữ / không mua đuổi
  - quantitative reasons
  - qualitative reasons
  - risks
  - confidence

Definition of Done:
- Query “FPT có đáng theo dõi không? Nêu lý do và rủi ro.” returns a useful answer.
- Answer cites evidence internally in response JSON.

Completion notes:
- Implemented advisory synthesizer consuming AnalyticalContext only and outputting status/reasons/risks/confidence text.
- Checks: advisory query returns structured rationale with risks.
- Limitation: confidence heuristic is static medium in narrative.

---

## Phase 8 - Guardrails

### T016 - Implement guardrails

Status: [x]

Goal:
Check answer before final output.

Required file:
- `backend/app/services/guardrails.py`

Required checks:
- Evidence exists for factual claims.
- Numeric claims come from analytics or DB.
- Add financial disclaimer.
- Warn if data is demo/mock data.
- Low confidence if evidence is missing.

Definition of Done:
- Every `/chat` response includes guardrails.
- Advisory answer includes disclaimer.
- Missing evidence lowers confidence or adds warning.

Completion notes:
- Implemented guardrails for evidence coverage, numeric-source checks, demo warning, and mandatory disclaimer.
- Checks: all /chat responses include guardrails + disclaimer.
- Limitation: claim parser is heuristic, not NLP-based.

---

### T017 - Add guardrails tests

Status: [x]

Goal:
Test guardrail behavior.

Required file:
- `backend/tests/test_guardrails.py`

Test:
- Empty evidence triggers warning.
- Advisory response gets disclaimer.
- Passed true when evidence exists.

Definition of Done:
- Tests pass.

Completion notes:
- Added guardrails tests (empty evidence warning, disclaimer presence, pass on evidence).
- Checks: pytest backend/tests/test_guardrails.py passed.
- Limitation: limited to core cases.

---

## Phase 9 - Chat Orchestration

### T018 - Wire `/chat` endpoint end-to-end

Status: [x]

Goal:
Connect router, services, evidence aggregator, advisory, and guardrails.

Required behavior:
- `/chat` handles all 5 demo queries.
- Returns response contract.
- Includes latency.
- Does not crash on unknown query.

Definition of Done:
- Manual tests for all 5 demo queries pass.
- JSON response is stable.
- Backend tests pass.

Completion notes:
- Wired /chat end-to-end (router -> services -> aggregation -> advisory -> guardrails) with latency and stable contract.
- Checks: manual 5-query /chat validation passed.
- Limitation: unknown queries return fallback message with low confidence path.

---

### T019 - Add simple in-memory cache

Status: [x]

Goal:
Add cache-aside behavior for repeated queries.

Required file:
- `backend/app/cache.py`

Required behavior:
- Cache normalized query responses.
- Include cache hit/miss in logs or evidence.
- Do not cache errors permanently.

Definition of Done:
- Repeating same query uses cache.
- Response still follows contract.

Completion notes:
- Added in-memory cache with normalized keys and cache-hit evidence marker.
- Checks: integrated in /chat path and contract preserved.
- Limitation: no TTL in MVP.

---

## Phase 10 - Frontend

### T020 - Create React chat UI

Status: [x]

Goal:
Create minimal frontend for demo.

Required behavior:
- Text input
- Send button
- Display answer
- Display intent, route, confidence
- Display evidence
- Display guardrail warnings

Definition of Done:
- `npm run dev` starts.
- User can ask all 5 demo queries from UI.

Completion notes:
- Built minimal React chat UI with input/send, answer, intent/route/confidence, evidence, guardrail warnings display.
- Checks: frontend install and build passed via npx vite build.
- Limitation: no streaming or state persistence.

---

### T021 - Add demo query buttons

Status: [x]

Goal:
Add clickable sample questions.

Required sample buttons:
- FPT niêm yết ở sàn nào?
- Giá FPT 3 tháng gần đây thế nào?
- Tính RSI14 và SMA20 của FPT.
- Tin tức gần đây về HPG là tích cực hay tiêu cực?
- FPT có đáng theo dõi không? Nêu lý do và rủi ro.

Definition of Done:
- Clicking a button sends the query.
- Result renders correctly.

Completion notes:
- Added demo query buttons and click-to-send behavior for all 5 required prompts.
- Checks: button flow implemented in App.jsx.
- Limitation: sample text uses ASCII Vietnamese for stability.

---

## Phase 11 - Docs and Demo

### T022 - Write architecture docs

Status: [x]

Goal:
Document the demo architecture.

Required file:
- `docs/architecture.md`

Must include:
- Mermaid diagram
- Explanation of direct path
- Explanation of analytics path
- Explanation of RAG path
- Explanation of advisory path
- Guardrails description
- What is mocked in demo

Definition of Done:
- Document is readable.
- Diagram renders in Markdown viewers that support Mermaid.

Completion notes:
- Wrote architecture doc with Mermaid flow and path explanations + mock scope.
- Checks: docs/architecture.md updated.
- Limitation: describes keyword-RAG fallback in current environment.

---

### T023 - Write demo script

Status: [x]

Goal:
Create a 5-minute presentation/demo script.

Required file:
- `docs/demo_script.md`

Must include:
1. Architecture introduction
2. Demo query 1: company info
3. Demo query 2: market data
4. Demo query 3: technical analytics
5. Demo query 4: news sentiment
6. Demo query 5: advisory synthesis
7. Limitations and next steps

Definition of Done:
- Script can be followed during presentation.

Completion notes:
- Added 5-minute demo script covering intro, 5 queries, limitations, next steps.
- Checks: docs/demo_script.md created.
- Limitation: presenter timing may vary by environment latency.

---

### T024 - Update README

Status: [x]

Goal:
Make the project easy to run.

README must include:
- Project purpose
- Architecture summary
- Setup backend
- Seed database
- Run tests
- Run frontend
- Demo queries
- Limitations
- Disclaimer

Definition of Done:
- A new developer can run the demo from README.

Completion notes:
- Updated README with purpose, architecture summary, setup, seed, tests, frontend run, demo queries, limitations, disclaimer.
- Checks: commands validated in this session (except npm run dev interactive).
- Limitation: frontend runtime check used build due sandbox process constraints.

---

## Phase 12 - Final Validation

### T025 - Final end-to-end test

Status: [x]

Goal:
Validate the complete demo.

Checklist:
- Backend starts.
- Frontend starts.
- Database seeded.
- Tests pass.
- All 5 demo queries work.
- Guardrail disclaimer appears.
- Evidence appears.
- README is accurate.

Definition of Done:
- Complete demo is ready for presentation.

Completion notes:
- Final validation completed: backend start, seed, tests, frontend build, and all 5 demo queries routed correctly with disclaimer/evidence.
- Checks: pytest -q (11 passed), /health and /chat manual checks, npx vite build passed.
- Limitation: realtime feeds and production infra intentionally out of scope.

---

# 8. Codex Operating Prompt

Use this prompt when starting Codex:

```txt
Read CODEX_TASKS.md.

Work strictly task by task.

For each task:
1. Mark the task as in progress.
2. Implement only that task.
3. Run relevant tests or checks.
4. Fix any errors.
5. Mark the task as done only if its Definition of Done passes.
6. Add short completion notes.
7. Move to the next task.

Do not skip tasks.
Do not over-engineer.
Do not use LLM logic for numeric calculations.
Keep the demo simple and runnable locally.
```

---

# 9. Safety and Financial Disclaimer

Every advisory-style output must include:

```txt
Thông tin này chỉ phục vụ mục đích tham khảo và demo hệ thống, không phải khuyến nghị đầu tư cá nhân hóa. Người dùng cần tự đánh giá rủi ro hoặc tham khảo chuyên gia tài chính trước khi ra quyết định.
```

---

# 10. MVP Boundaries

This demo intentionally does not include:

```txt
Realtime market data
Full HOSE/HNX ingestion
Corporate action adjustment
Portfolio optimization
Personalized financial advice
Production-grade authentication
Production-grade observability
ClickHouse/Kafka/Kubernetes
```

These can be added after the MVP is complete.

