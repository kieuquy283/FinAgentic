from __future__ import annotations

import csv
import json
import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db import ensure_runtime_tables
from app.ingestion.ingestion_utils import bootstrap_schema, now_utc_iso

SEED_DATA_DIR = ROOT / "data"
RUNTIME_DATA_DIR = ROOT / "backend" / "data"
DB_PATH = RUNTIME_DATA_DIR / "demo_seed.db"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def seed_sqlite() -> None:
    RUNTIME_DATA_DIR.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        os.chmod(DB_PATH, 0o666)
        DB_PATH.unlink()

    companies = load_json(SEED_DATA_DIR / "companies.json")
    news = load_json(SEED_DATA_DIR / "news.json")
    reports = load_json(SEED_DATA_DIR / "reports.json")

    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    cur.executescript(
        """
        CREATE TABLE companies (
            ticker TEXT PRIMARY KEY,
            company_name TEXT NOT NULL,
            exchange TEXT NOT NULL,
            sector TEXT NOT NULL,
            description TEXT NOT NULL,
            source TEXT NOT NULL,
            source_url TEXT,
            fetched_at TEXT NOT NULL
        );

        CREATE TABLE prices (
            ticker TEXT NOT NULL,
            date TEXT NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume INTEGER NOT NULL,
            source TEXT NOT NULL,
            source_url TEXT,
            fetched_at TEXT NOT NULL,
            data_date TEXT,
            PRIMARY KEY (ticker, date)
        );

        CREATE TABLE financial_ratios (
            ticker TEXT NOT NULL,
            metric TEXT NOT NULL,
            value REAL,
            period TEXT,
            source TEXT NOT NULL,
            source_url TEXT,
            fetched_at TEXT NOT NULL,
            data_date TEXT,
            PRIMARY KEY (ticker, metric, period)
        );

        CREATE TABLE news (
            id TEXT PRIMARY KEY,
            ticker TEXT NOT NULL,
            date TEXT NOT NULL,
            title TEXT,
            snippet TEXT,
            url TEXT,
            published_at TEXT,
            source TEXT NOT NULL,
            source_url TEXT,
            fetched_at TEXT NOT NULL,
            content TEXT NOT NULL
        );

        CREATE TABLE reports (
            id TEXT PRIMARY KEY,
            ticker TEXT NOT NULL,
            date TEXT NOT NULL,
            source TEXT NOT NULL,
            content TEXT NOT NULL
        );
        """
    )

    fetched_at = now_utc_iso()
    cur.executemany(
        "INSERT INTO companies VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [(c["ticker"], c["company_name"], c["exchange"], c["sector"], c["description"], "demo_seed", "local_seed_json", fetched_at) for c in companies],
    )

    with (SEED_DATA_DIR / "prices.csv").open("r", encoding="utf-8-sig") as f:
        rows = [
            (
                r["ticker"],
                r["date"],
                float(r["open"]),
                float(r["high"]),
                float(r["low"]),
                float(r["close"]),
                int(r["volume"]),
                "demo_seed",
                "local_seed_csv",
                fetched_at,
                r["date"],
            )
            for r in csv.DictReader(f)
        ]
    cur.executemany("INSERT INTO prices VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)

    cur.executemany(
        "INSERT INTO news VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [(n["id"], n["ticker"], n["date"], n["content"], "", "", n["date"], n["source"], "local_seed_json", fetched_at, n["content"]) for n in news],
    )
    cur.executemany("INSERT INTO reports VALUES (?, ?, ?, ?, ?)", [(r["id"], r["ticker"], r["date"], r["source"], r["content"]) for r in reports])

    conn.commit()
    conn.close()
    ensure_runtime_tables()
    bootstrap_schema()


if __name__ == "__main__":
    seed_sqlite()
    print(f"Seeded SQLite at {DB_PATH}")
