# Real Data Ingestion

## Setup
```bash
cd backend
python -m pip install -r requirements.txt
```

## Commands
Full run:
```bash
python scripts/ingest_real_data.py --tickers FPT HPG VCB VNM
```

Prices only:
```bash
python scripts/ingest_real_data.py --tickers FPT --prices-only
```

News only:
```bash
python scripts/ingest_real_data.py --tickers HPG --news-only
```

Direct module commands:
```bash
python -m app.ingestion.market_ingestion
python -m app.ingestion.company_ingestion
```

## Expected tables
- `companies`
- `prices`
- `financial_ratios`
- `news`
- `raw_ingestion_items`
- `ingestion_logs`
- `source_metadata`

## Verify real data was loaded
Run quick SQL checks:
```sql
SELECT ticker, COUNT(*) FROM prices GROUP BY ticker;
SELECT ticker, source, COUNT(*) FROM news GROUP BY ticker, source;
SELECT source, status, COUNT(*) FROM ingestion_logs GROUP BY source, status;
```

Expected:
- at least `FPT` and `HPG` price rows when source/network is available
- ingestion logs recorded for each ticker/job

## Troubleshooting
- `vnstock` install/import fails:
  - verify Python env and `pip install -r backend/requirements.txt`
  - capture exact error from ingestion output/logs
- source/network blocked:
  - ingestion logs `error` per ticker and continues
  - runtime remains DB-only and should still run with fallback seed data
- no real data rows:
  - rerun ingestion command with internet access
  - check `ingestion_logs.message` for root cause

Observed in this environment:
- `vnstock` runtime error:
  - `[WinError 5] Access is denied: 'C:\\Users\\mrdo_\\.vnstock'`
  - Mitigation: ensure process has permission to create/use vnstock cache folder.
- News fetch network error:
  - `HTTPSConnectionPool(... ProxyError ... 127.0.0.1:9 refused)`
  - Mitigation: disable invalid proxy settings or run in a network-open environment.

## Runtime behavior note
- `/chat` never calls external websites/APIs directly.
- If real data is missing and seed/demo rows are used, guardrails show:
  - `Real data missing; using demo fallback data.`
