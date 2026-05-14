# Real Data Validation

Date: 2026-05-14

## Commands run
- DB inspection:
  - `python -` (sqlite queries against `backend/data/demo_seed.db`)
- Runtime behavior checks:
  - `pytest -q tests/test_ingestion.py::test_runtime_chat_no_external_api`
  - backend code scan for network calls:
    - `Get-ChildItem -Recurse -File backend/app | Select-String -Pattern "requests\\.|httpx\\.|urllib\\.request|aiohttp|vnstock"`
- `/chat` functional checks:
  - start `uvicorn app.main:app`
  - send 5 demo queries via `Invoke-RestMethod`

## Row counts by table/source

### Table counts
- `companies`: 4
- `prices`: 361
- `financial_ratios`: 0
- `news`: 5
- `raw_ingestion_items`: 0
- `ingestion_logs`: 23
- `source_metadata`: 5

### `prices` by source
- `unknown`: 360
- `vnstock`: 1

### `news` by source
- `mock_news`: 5

### `ingestion_logs` by source/status
- `google_news_rss` / `error`: 8
- `vnstock` / `error`: 5
- `fallback_static_metadata` / `fallback`: 4
- `vnstock_finance` / `skipped`: 4
- `cafef` / `error`: 2

## Sample rows

### `prices` sample
- `FPT | 2026-05-14 | close=108.88 | source=unknown | fetched_at=''`
- `HPG | 2026-05-14 | close=24.53 | source=unknown | fetched_at=''`
- `VCB | 2026-05-14 | close=87.76 | source=unknown | fetched_at=''`
- `VNM | 2026-05-14 | close=65.31 | source=unknown | fetched_at=''`

### `news` sample
- `FPT | 2026-05-11 | source=mock_news | content='Mang xuat khau phan mem cua FPT tang truong...'`
- `HPG | 2026-05-10 | source=mock_news | content='HPG doi mat ap luc bien loi nhuan...'`

### Ingestion error sample
- `vnstock`: `[WinError 5] Access is denied: 'C:\\Users\\mrdo_\\.vnstock'`
- `cafef`: proxy/network blocked (`127.0.0.1:9` connection refused)

## `/chat` outputs summary

All 5 required demo queries returned successfully with:
- intent/route/confidence present
- evidence present (6-7 items)
- guardrails present
- disclaimer present in answer

Observed routing:
- `FPT niêm yết ở sàn nào?` -> `company_info/direct`
- `Giá FPT 3 tháng gần đây thế nào?` -> `market_data/direct`
- `Tính RSI14 và SMA20 của FPT.` -> `technical_analysis/analytics`
- `Tin tức gần đây về HPG là tích cực hay tiêu cực?` -> `news_sentiment/rag`
- `FPT có đáng theo dõi không? Nêu lý do và rủi ro.` -> `investment_advisory/advisory`

Guardrail warning currently shown:
- `Real data missing; using demo fallback data.`
- `Du lieu dang o che do demo/mock.`

## Validation against requested checks

1. `prices` table contains non-demo ingested rows: **PASS (partial)**
- `source='vnstock'` exists (1 row), majority remains legacy/demo-style rows (`unknown`).

2. `news` table contains real ingested rows or blocked-source errors: **PASS (blocked-source path)**
- No real rows loaded; blocked-source errors are recorded in `ingestion_logs`.

3. `/chat` market query reads prices from DB: **PASS**
- `MarketDataService` reads `prices` table only.

4. `/chat` analytics query computes SMA/RSI from DB prices: **PASS**
- `EvidenceAggregator` loads DB closes, `AnalyticsService` computes indicators in Python.

5. `/chat` news query reads ingested news: **PASS (DB path), DATA LIMITED**
- `RagService` reads `news` table only; current rows are `mock_news`.

6. No external API calls happen during `/chat`: **PASS**
- Targeted test passes: `test_runtime_chat_no_external_api`.
- Code scan shows network clients only in ingestion modules, not runtime services.

7. Guardrails source/freshness/demo fallback warning: **PASS**
- Demo fallback warning appears correctly when real provenance is missing.

## Failures and fixes

### Failure 1: schema mismatch on existing DB
- Symptoms:
  - `source_metadata has no column limitations`
  - `ingestion_logs has no column ingestion_type`
  - `prices has no column source`
- Fix:
  - added compatibility migration in `ensure_runtime_tables()` to `ALTER TABLE` missing columns.

### Failure 2: ingestion log insert failing with legacy `entity` constraint
- Symptom:
  - `NOT NULL constraint failed: ingestion_logs.entity`
- Fix:
  - made log insert adaptive to actual `ingestion_logs` columns detected by `PRAGMA`.

## Final verdict
- The app is **not purely mock in architecture path**: runtime is DB-only, ingestion jobs are separate, guardrails surface fallback status.
- The app is **still mostly demo-backed in data content** in this environment due source/network blocks (`vnstock` permission and external proxy refusal).
- Real-data ingestion framework is functioning and logs exact failures cleanly; to fully transition from mock content, environment access issues must be resolved and ingestion rerun.
