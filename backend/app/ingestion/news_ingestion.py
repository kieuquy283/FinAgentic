from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from sqlalchemy import text

from app.db import get_engine
from app.ingestion.ingestion_utils import (
    IngestionLog,
    bootstrap_schema,
    insert_ingestion_log,
    match_ticker,
    now_utc_iso,
    retry,
    sha_id,
    upsert_raw_item,
    upsert_source_metadata,
)

HEADERS = {"User-Agent": "FinanceAgenticRAG/1.0 (demo ingestion; contact local-admin)"}

SOURCE_URLS = {
    "cafef_market": "https://cafef.vn/thi-truong-chung-khoan.chn",
}


@dataclass
class NewsRecord:
    id: str
    ticker: str
    date: str
    title: str
    snippet: str
    url: str
    published_at: str | None
    source: str
    source_url: str
    fetched_at: str
    content: str


def fetch_cafef_news_items(max_items: int = 40) -> list[dict]:
    resp = requests.get(SOURCE_URLS["cafef_market"], headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    out: list[dict] = []
    for a in soup.select("a[href]"):
        href = a.get("href", "").strip()
        title = " ".join(a.get_text(" ", strip=True).split())
        if not href or not title or len(title) < 10:
            continue
        if ".chn" not in href:
            continue
        full_url = href if href.startswith("http") else urljoin("https://cafef.vn", href)
        out.append({"title": title, "url": full_url, "snippet": "", "published_at": None, "source": "cafef"})
        if len(out) >= max_items:
            break
    return out


def deduplicate_news(items: list[dict]) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for item in items:
        key = f"{item.get('url','')}|{item.get('title','')}".strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def normalize_news_items(items: list[dict], tickers: list[str]) -> list[NewsRecord]:
    today = datetime.now(timezone.utc).date().isoformat()
    allowed = set(tickers)
    out: list[NewsRecord] = []
    for item in deduplicate_news(items):
        title = str(item.get("title", "")).strip()
        ticker = match_ticker(title) or match_ticker(str(item.get("snippet", "")) or "")
        if not ticker or ticker not in allowed:
            continue
        url = str(item.get("url", "")).strip()
        snippet = str(item.get("snippet", "")).strip()
        pub = item.get("published_at")
        date = str(pub)[:10] if pub else today
        news_id = sha_id([ticker, title, url])
        content = f"{title}. {snippet}".strip()
        out.append(
            NewsRecord(
                id=news_id,
                ticker=ticker,
                date=date,
                title=title,
                snippet=snippet,
                url=url,
                published_at=str(pub) if pub else None,
                source=str(item.get("source", "cafef")),
                source_url=SOURCE_URLS["cafef_market"],
                fetched_at=now_utc_iso(),
                content=content,
            )
        )
    return out


def upsert_news(rows: list[NewsRecord]) -> int:
    if not rows:
        return 0
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO news (id, ticker, date, title, snippet, url, published_at, source, source_url, fetched_at, content)
                VALUES (:id, :ticker, :date, :title, :snippet, :url, :published_at, :source, :source_url, :fetched_at, :content)
                ON CONFLICT(id) DO UPDATE SET
                    ticker = excluded.ticker,
                    date = excluded.date,
                    title = excluded.title,
                    snippet = excluded.snippet,
                    url = excluded.url,
                    published_at = excluded.published_at,
                    source = excluded.source,
                    source_url = excluded.source_url,
                    fetched_at = excluded.fetched_at,
                    content = excluded.content
                """
            ),
            [r.__dict__ for r in rows],
        )
    return len(rows)


def run_news_ingestion(tickers: list[str], max_items: int = 40) -> IngestionLog:
    bootstrap_schema()
    upsert_source_metadata(
        source="cafef",
        source_type="news",
        url=SOURCE_URLS["cafef_market"],
        limitations="HTML layout can change; published date may be missing from list page.",
        legal_caveats="Respect publisher terms; store snippets/metadata only.",
        fallback_behavior="If source fetch fails, log error and keep previous local DB news.",
    )
    try:
        raw_items = retry(lambda: fetch_cafef_news_items(max_items=max_items), attempts=2)
        norm = normalize_news_items(raw_items, tickers)
        for item in raw_items:
            upsert_raw_item(
                item_id=sha_id([item.get("title", ""), item.get("url", "")]),
                ingestion_type="news",
                ticker=match_ticker(str(item.get("title", ""))),
                source="cafef",
                source_url=SOURCE_URLS["cafef_market"],
                data_date=None,
                payload=item,
            )
        up = upsert_news(norm)
        log = IngestionLog("news", None, "cafef", "ok" if up > 0 else "empty", len(raw_items), up, "")
    except Exception as exc:  # noqa: BLE001
        log = IngestionLog("news", None, "cafef", "error", 0, 0, str(exc))
    insert_ingestion_log(log)
    return log


if __name__ == "__main__":
    r = run_news_ingestion(["FPT", "HPG", "VCB", "VNM"], max_items=40)
    print(f"[{r.status}] news raw={r.records_raw} upserted={r.records_upserted} msg={r.message}")
