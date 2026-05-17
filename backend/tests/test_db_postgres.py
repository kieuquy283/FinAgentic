from pathlib import Path

from sqlalchemy import create_engine, text

from app import db


def test_get_engine_uses_database_url_when_set(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///backend/data/test_db_url.db")
    db.reset_engine_for_tests()
    engine = db.get_engine()
    assert str(engine.url).startswith("sqlite:///backend/data/test_db_url.db")


def test_get_engine_falls_back_to_sqlite(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    db.reset_engine_for_tests()
    engine = db.get_engine()
    assert str(engine.url).startswith("sqlite:///")


def test_get_engine_singleton(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///backend/data/test_db_singleton.db")
    db.reset_engine_for_tests()
    e1 = db.get_engine()
    e2 = db.get_engine()
    assert e1 is e2


def test_prices_index_exists(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///backend/data/test_db_index.db")
    db.reset_engine_for_tests()
    db.ensure_runtime_tables()
    assert db.has_prices_index() is True


def test_direct_sma_with_database_url_sqlite(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'direct_sma.db'}")
    db.reset_engine_for_tests()
    db.ensure_runtime_tables()

    engine = db.get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO prices (ticker, date, open, high, low, close, volume, source, fetched_at)
                VALUES (:ticker, :date, :open, :high, :low, :close, :volume, 'test', '2026-05-17')
                """
            ),
            [
                {
                    "ticker": "FPT",
                    "date": f"2026-01-{i:02d}",
                    "open": 100 + i,
                    "high": 101 + i,
                    "low": 99 + i,
                    "close": 100 + i,
                    "volume": 1000 + i,
                }
                for i in range(1, 25)
            ],
        )

    from app.main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    resp = client.post("/chat", json={"query": "SMA20 FPT"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "technical_analysis"
    assert "SMA20" in data["answer"]


def test_migration_script_copies_prices(tmp_path: Path):
    from scripts.migrate_sqlite_to_postgres import _copy_table

    src = create_engine(f"sqlite:///{tmp_path / 'src.db'}", future=True)
    dst = create_engine(f"sqlite:///{tmp_path / 'dst.db'}", future=True)

    ddl = """
    CREATE TABLE prices (
      ticker TEXT NOT NULL,
      date TEXT NOT NULL,
      open REAL NOT NULL,
      high REAL NOT NULL,
      low REAL NOT NULL,
      close REAL NOT NULL,
      volume INTEGER NOT NULL,
      source TEXT,
      source_url TEXT,
      fetched_at TEXT,
      data_date TEXT,
      PRIMARY KEY (ticker, date)
    )
    """
    with src.begin() as conn:
        conn.execute(text(ddl))
        conn.execute(
            text(
                "INSERT INTO prices (ticker,date,open,high,low,close,volume,source,fetched_at) VALUES ('FPT','2026-01-01',1,1,1,1,1,'s','t')"
            )
        )
    with dst.begin() as conn:
        conn.execute(text(ddl))

    inserted, total = _copy_table(src, dst, "prices")
    assert total == 1
    assert inserted >= 1

    with dst.connect() as conn:
        row = conn.execute(text("SELECT COUNT(*) AS c FROM prices")).mappings().first()
    assert int(row["c"]) == 1
