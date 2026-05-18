from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

BACKEND_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BACKEND_DIR / "data"
DB_PATH = DATA_DIR / "demo_seed.db"
_ENGINE: Engine | None = None


def get_database_url() -> str:
    db_url = os.getenv("DATABASE_URL", "").strip()
    if db_url and db_url.startswith("postgresql://"):
        raise RuntimeError("Use psycopg v3 URL format: postgresql+psycopg://...")
    if db_url:
        return db_url
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{DB_PATH}"


def get_engine() -> Engine:
    global _ENGINE
    if _ENGINE is None:
        database_url = get_database_url()
        connect_args: dict = {}
        if database_url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
        _ENGINE = create_engine(
            database_url,
            future=True,
            pool_pre_ping=True,
            connect_args=connect_args,
        )
    return _ENGINE


def reset_engine_for_tests() -> None:
    global _ENGINE
    if _ENGINE is not None:
        _ENGINE.dispose()
    _ENGINE = None


def get_db_dialect() -> str:
    return get_engine().dialect.name


def get_database_target_public() -> str:
    engine = get_engine()
    url = engine.url
    if engine.dialect.name == "sqlite":
        db_name = str(url.database or DB_PATH)
        return str(Path(db_name).resolve())
    host = url.host or "localhost"
    port = url.port or 5432
    database = url.database or ""
    return f"{host}:{port}/{database}"


def is_database_url_set() -> bool:
    return bool(os.getenv("DATABASE_URL", "").strip())


def get_database_host_masked() -> str:
    engine = get_engine()
    if engine.dialect.name == "sqlite":
        return "local-file"
    host = str(engine.url.host or "localhost")
    if len(host) <= 4:
        return "*" * len(host)
    return f"{host[:2]}***{host[-2:]}"


def table_exists(table: str) -> bool:
    engine = get_engine()
    with engine.connect() as conn:
        if engine.dialect.name == "sqlite":
            row = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name=:table"),
                {"table": table},
            ).mappings().first()
            return bool(row)
        row = conn.execute(
            text("SELECT to_regclass(:table_name) AS tbl"),
            {"table_name": table},
        ).mappings().first()
        return bool(row and row.get("tbl"))


def ensure_runtime_tables() -> None:
    engine = get_engine()
    dialect = engine.dialect.name

    ddl_common = [
        """
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
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS prices (
            ticker TEXT NOT NULL,
            date TEXT NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume BIGINT NOT NULL,
            source TEXT NOT NULL DEFAULT 'unknown',
            source_url TEXT,
            fetched_at TEXT NOT NULL DEFAULT '',
            data_date TEXT,
            PRIMARY KEY (ticker, date)
        )
        """,
        """
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
        )
        """,
        """
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
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS reports (
            id TEXT PRIMARY KEY,
            ticker TEXT NOT NULL,
            date TEXT NOT NULL,
            source TEXT NOT NULL,
            content TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS raw_ingestion_items (
            id TEXT PRIMARY KEY,
            ingestion_type TEXT NOT NULL,
            ticker TEXT,
            source TEXT NOT NULL,
            source_url TEXT,
            fetched_at TEXT NOT NULL,
            data_date TEXT,
            payload TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS source_metadata (
            source TEXT PRIMARY KEY,
            source_type TEXT NOT NULL,
            url TEXT,
            limitations TEXT,
            legal_caveats TEXT,
            fallback_behavior TEXT,
            updated_at TEXT NOT NULL
        )
        """,
    ]

    if dialect == "postgresql":
        ingestion_logs_ddl = """
        CREATE TABLE IF NOT EXISTS ingestion_logs (
            id BIGSERIAL PRIMARY KEY,
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
        )
        """
    else:
        ingestion_logs_ddl = """
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
        )
        """

    with engine.begin() as conn:
        for stmt in ddl_common + [ingestion_logs_ddl]:
            conn.execute(text(stmt))
        if dialect == "sqlite":
            _ensure_compatible_columns_sqlite(conn)
        _create_prices_indexes(conn)


def _ensure_compatible_columns_sqlite(conn) -> None:
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


def _create_prices_indexes(conn) -> None:
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_prices_ticker_date ON prices(ticker, date DESC)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_prices_ticker_date_asc ON prices(ticker, date)"))


def ensure_prices_index() -> None:
    engine = get_engine()
    with engine.begin() as conn:
        _create_prices_indexes(conn)


def has_prices_index() -> bool:
    engine = get_engine()
    dialect = engine.dialect.name
    with engine.connect() as conn:
        if dialect == "sqlite":
            rows = conn.execute(text("PRAGMA index_list('prices')")).mappings().all()
            names = {str(r.get("name")) for r in rows}
        else:
            rows = conn.execute(
                text(
                    "SELECT indexname FROM pg_indexes WHERE schemaname = current_schema() AND tablename = 'prices'"
                )
            ).mappings().all()
            names = {str(r.get("indexname")) for r in rows}
    return "idx_prices_ticker_date" in names
