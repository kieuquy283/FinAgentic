from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.ingestion.company_ingestion import run_company_ingestion
from app.ingestion.finance_ingestion import run_finance_ingestion
from app.ingestion.market_ingestion import run_market_ingestion
from app.ingestion.news_ingestion import run_news_ingestion


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest real data for selected Vietnamese tickers")
    parser.add_argument("--tickers", nargs="+", default=["FPT", "HPG", "VCB", "VNM"])
    parser.add_argument("--prices-only", action="store_true")
    parser.add_argument("--news-only", action="store_true")
    args = parser.parse_args()

    tickers = [t.upper() for t in args.tickers]
    if args.prices_only and args.news_only:
        raise SystemExit("Cannot use --prices-only and --news-only together")

    if args.prices_only:
        market_logs = run_market_ingestion(tickers)
        for l in market_logs:
            print(f"[{l.status}] market:{l.ticker} raw={l.records_raw} upserted={l.records_upserted} {l.message}")
        return

    if args.news_only:
        log = run_news_ingestion(tickers)
        print(f"[{log.status}] news raw={log.records_raw} upserted={log.records_upserted} {log.message}")
        return

    company_logs = run_company_ingestion(tickers)
    market_logs = run_market_ingestion(tickers)
    finance_logs = run_finance_ingestion(tickers)
    news_log = run_news_ingestion(tickers)

    for l in company_logs + market_logs + finance_logs:
        print(f"[{l.status}] {l.ingestion_type}:{l.ticker} raw={l.records_raw} upserted={l.records_upserted} {l.message}")
    print(f"[{news_log.status}] news raw={news_log.records_raw} upserted={news_log.records_upserted} {news_log.message}")


if __name__ == "__main__":
    main()
