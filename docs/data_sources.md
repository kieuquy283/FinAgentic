# Data Sources

## 1) vnstock
- Source name: `vnstock`
- URL: `https://github.com/thinh-vu/vnstock`
- Data type:
  - OHLCV historical prices
  - company profile
  - financial ratios (if endpoint available)
- Used for:
  - `prices` table
  - `companies` table
  - `financial_ratios` table
- Limitations:
  - endpoint behavior/schema can vary
  - some tickers/fields may return empty values
- Legal/usage caveats:
  - use for analysis/demo; verify redistribution and licensing terms
- Fallback behavior:
  - company ingestion falls back to static metadata (`fallback_static_metadata`)
  - market/finance ingestion logs per-ticker errors and continues

## 2) CafeF public market/news page
- Source name: `cafef`
- URL: `https://cafef.vn/thi-truong-chung-khoan.chn`
- Data type:
  - public article links/headlines/snippets from listing page
- Used for:
  - `news` table (headline-level snippets for RAG/news sentiment)
- Limitations:
  - HTML structure may change
  - published date may be unavailable on listing-only parse
- Legal/usage caveats:
  - keep snippets/metadata only; respect publisher terms
- Fallback behavior:
  - if blocked/fails, ingestion logs error and keeps existing local DB data

## 3) Official disclosure sources
- Status: documented only
- Reason:
  - stable/simple integration not implemented in this MVP scope
