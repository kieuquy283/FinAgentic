from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

SCRIPT_DIR = Path(__file__).resolve().parent
LOCAL_BACKEND_DIR = SCRIPT_DIR.parent
if str(LOCAL_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(LOCAL_BACKEND_DIR))

from app.db import BACKEND_DIR, ensure_runtime_tables, reset_engine_for_tests

TABLES = [
    "companies",
    "prices",
    "financial_ratios",
    "news",
    "reports",
    "raw_ingestion_items",
    "ingestion_logs",
    "source_metadata",
]

PK_MAP = {
    "companies": ["ticker"],
    "prices": ["ticker", "date"],
    "financial_ratios": ["ticker", "metric", "period"],
    "news": ["id"],
    "reports": ["id"],
    "raw_ingestion_items": ["id"],
    "ingestion_logs": ["id"],
    "source_metadata": ["source"],
}


def _build_insert_sql(table: str, columns: list[str], dialect: str) -> str:
    cols = ", ".join(columns)
    vals = ", ".join(f":{c}" for c in columns)
    if dialect == "postgresql":
        pk_cols = PK_MAP.get(table, [])
        conflict = ", ".join(pk_cols)
        if conflict:
            return f"INSERT INTO {table} ({cols}) VALUES ({vals}) ON CONFLICT ({conflict}) DO NOTHING"
    return f"INSERT OR IGNORE INTO {table} ({cols}) VALUES ({vals})"


def _table_exists(engine: Engine, table: str) -> bool:
    with engine.connect() as conn:
        if engine.dialect.name == "sqlite":
            row = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name=:table"), {"table": table}
            ).first()
            return row is not None
        row = conn.execute(
            text("SELECT to_regclass(:table_name) AS tbl"), {"table_name": table}
        ).mappings().first()
        return bool(row and row.get("tbl"))


def _truncate_target(engine: Engine, table: str) -> None:
    with engine.begin() as conn:
        if engine.dialect.name == "postgresql":
            conn.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE"))
        else:
            conn.execute(text(f"DELETE FROM {table}"))


def _copy_table(src_engine: Engine, dst_engine: Engine, table: str, batch_size: int = 1000) -> tuple[int, int]:
    if not _table_exists(src_engine, table):
        return 0, 0

    inserted = 0
    total = 0
    with src_engine.connect() as src_conn:
        rows = src_conn.execute(text(f"SELECT * FROM {table}")).mappings().all()

    if not rows:
        return 0, 0

    cols = list(rows[0].keys())
    sql = _build_insert_sql(table, cols, dst_engine.dialect.name)

    with dst_engine.begin() as dst_conn:
        for i in range(0, len(rows), batch_size):
            batch = [dict(r) for r in rows[i : i + batch_size]]
            res = dst_conn.execute(text(sql), batch)
            total += len(batch)
            if res.rowcount and res.rowcount > 0:
                inserted += res.rowcount

    return inserted, total


def migrate(sqlite_db_path: Path, truncate: bool) -> None:
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL is required and must point to PostgreSQL")
    if not database_url.startswith("postgresql"):
        raise RuntimeError("DATABASE_URL must be a postgresql URL for migration target")

    src_engine = create_engine(f"sqlite:///{sqlite_db_path}", future=True)

    # Rebind app db engine to DATABASE_URL for ensure_runtime_tables.
    reset_engine_for_tests()
    ensure_runtime_tables()

    from app.db import get_engine, ensure_prices_index

    dst_engine = get_engine()

    if truncate:
        for table in TABLES:
            _truncate_target(dst_engine, table)

    print(f"Migrating from SQLite: {sqlite_db_path}")
    print("Migrating to PostgreSQL target from DATABASE_URL")
    for table in TABLES:
        ins, total = _copy_table(src_engine, dst_engine, table)
        with dst_engine.connect() as conn:
            cnt = conn.execute(text(f"SELECT COUNT(*) AS c FROM {table}")).mappings().first()
        print(f"{table}: source_rows={total}, inserted={ins}, target_count={int(cnt['c']) if cnt else 0}")

    ensure_prices_index()
    print("Migration completed. Ensured prices indexes.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate SQLite demo DB to PostgreSQL")
    parser.add_argument("--truncate", action="store_true", help="Truncate target tables before import")
    args = parser.parse_args()

    default_sqlite = BACKEND_DIR / "data" / "demo_seed.db"
    sqlite_db_path = Path(os.getenv("SQLITE_DB_PATH", str(default_sqlite)))
    migrate(sqlite_db_path=sqlite_db_path, truncate=args.truncate)


if __name__ == "__main__":
    main()
