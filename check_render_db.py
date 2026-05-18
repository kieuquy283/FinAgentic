import os
from sqlalchemy import create_engine, text

engine = create_engine(os.environ["DATABASE_URL"])

with engine.connect() as conn:
    prices = conn.execute(text("select count(*) from prices")).scalar()
    fpt = conn.execute(text("select count(*) from prices where ticker = 'FPT'")).scalar()
    latest = conn.execute(text("select max(date) from prices where ticker = 'FPT'")).scalar()

print("prices=", prices)
print("fpt=", fpt)
print("latest_fpt_date=", latest)
