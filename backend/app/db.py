from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

BACKEND_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BACKEND_DIR / "data"
DB_PATH = DATA_DIR / "demo_seed.db"
_ENGINE: Engine | None = None


def get_engine():
    global _ENGINE
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if _ENGINE is None:
        _ENGINE = create_engine(f"sqlite:///{DB_PATH}", future=True)
    return _ENGINE


def ensure_runtime_tables() -> None:
    engine = get_engine()
    ddl = """
    CREATE TABLE IF NOT EXISTS companies (
        ticker TEXT PRIMARY KEY,
        company_name TEXT NOT NULL,
        name TEXT,
        exchange TEXT NOT NULL,
        sector TEXT NOT NULL,
        industry TEXT,
        description TEXT NOT NULL,
        source TEXT NOT NULL DEFAULT 'unknown',
        source_url TEXT,
        fetched_at TEXT NOT NULL DEFAULT ''
    );

    CREATE TABLE IF NOT EXISTS prices (
        ticker TEXT NOT NULL,
        date TEXT NOT NULL,
        open REAL NOT NULL,
        high REAL NOT NULL,
        low REAL NOT NULL,
        close REAL NOT NULL,
        volume INTEGER NOT NULL,
        source TEXT NOT NULL DEFAULT 'unknown',
        source_url TEXT,
        fetched_at TEXT NOT NULL DEFAULT '',
        data_date TEXT,
        PRIMARY KEY (ticker, date)
    );

    CREATE TABLE IF NOT EXISTS financial_ratios (
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

    CREATE TABLE IF NOT EXISTS news (
        id TEXT PRIMARY KEY,
        ticker TEXT NOT NULL,
        date TEXT NOT NULL,
        title TEXT,
        snippet TEXT,
        url TEXT,
        published_at TEXT,
        source TEXT NOT NULL,
        source_url TEXT,
        fetched_at TEXT NOT NULL DEFAULT '',
        content TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS reports (
        id TEXT PRIMARY KEY,
        ticker TEXT NOT NULL,
        date TEXT NOT NULL,
        source TEXT NOT NULL,
        content TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS raw_ingestion_items (
        id TEXT PRIMARY KEY,
        ingestion_type TEXT NOT NULL,
        ticker TEXT,
        source TEXT NOT NULL,
        source_url TEXT,
        fetched_at TEXT NOT NULL,
        data_date TEXT,
        payload TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS ingestion_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT NOT NULL DEFAULT 'unknown',
        job_type TEXT,
        started_at TEXT,
        finished_at TEXT,
        run_at TEXT NOT NULL,
        ingestion_type TEXT NOT NULL,
        ticker TEXT,
        status TEXT NOT NULL,
        records_raw INTEGER NOT NULL,
        records_upserted INTEGER NOT NULL,
        message TEXT
    );

    CREATE TABLE IF NOT EXISTS source_metadata (
        source TEXT PRIMARY KEY,
        source_type TEXT NOT NULL,
        url TEXT,
        limitations TEXT,
        legal_caveats TEXT,
        fallback_behavior TEXT,
        updated_at TEXT NOT NULL
    );
    """
    with engine.begin() as conn:
        for stmt in [s.strip() for s in ddl.split(";") if s.strip()]:
            conn.execute(text(stmt))
        _ensure_compatible_columns(conn)


def _ensure_compatible_columns(conn) -> None:
    def has_col(table: str, col: str) -> bool:
        rows = conn.execute(text(f"PRAGMA table_info({table})")).mappings().all()
        return any(str(r.get("name")) == col for r in rows)

    alter_map = {
        "companies": [
            ("name", "TEXT"),
            ("source", "TEXT NOT NULL DEFAULT 'unknown'"),
            ("source_url", "TEXT"),
            ("fetched_at", "TEXT NOT NULL DEFAULT ''"),
            ("industry", "TEXT"),
        ],
        "prices": [
            ("source", "TEXT NOT NULL DEFAULT 'unknown'"),
            ("source_url", "TEXT"),
            ("fetched_at", "TEXT NOT NULL DEFAULT ''"),
            ("data_date", "TEXT"),
        ],
        "news": [
            ("title", "TEXT"),
            ("snippet", "TEXT"),
            ("url", "TEXT"),
            ("published_at", "TEXT"),
            ("source_url", "TEXT"),
            ("fetched_at", "TEXT NOT NULL DEFAULT ''"),
        ],
        "source_metadata": [
            ("source_type", "TEXT"),
            ("url", "TEXT"),
            ("limitations", "TEXT"),
            ("legal_caveats", "TEXT"),
            ("fallback_behavior", "TEXT"),
            ("updated_at", "TEXT"),
        ],
        "ingestion_logs": [
            ("source", "TEXT"),
            ("job_type", "TEXT"),
            ("started_at", "TEXT"),
            ("finished_at", "TEXT"),
            ("ingestion_type", "TEXT"),
            ("ticker", "TEXT"),
            ("status", "TEXT"),
            ("records_raw", "INTEGER"),
            ("records_upserted", "INTEGER"),
            ("message", "TEXT"),
        ],
        "raw_ingestion_items": [
            ("ingestion_type", "TEXT"),
            ("ticker", "TEXT"),
            ("source", "TEXT"),
            ("source_url", "TEXT"),
            ("fetched_at", "TEXT"),
            ("data_date", "TEXT"),
            ("payload", "TEXT"),
        ],
    }
    for table, cols in alter_map.items():
        for col, decl in cols:
            if not has_col(table, col):
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {decl}"))
