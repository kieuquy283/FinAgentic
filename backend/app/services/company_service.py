from __future__ import annotations

from sqlalchemy import text

from app.db import get_engine


class CompanyService:
    def get_company(self, ticker: str):
        if not ticker:
            return None
        engine = get_engine()
        with engine.connect() as conn:
            return conn.execute(
                text(
                    """
                    SELECT ticker, company_name, exchange, sector, description, source, fetched_at
                    FROM companies
                    WHERE ticker = :ticker
                    """
                ),
                {"ticker": ticker},
            ).mappings().first()
