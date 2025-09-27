# ...existing code...
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker, declarative_base
import os
import time
from sqlalchemy.exc import OperationalError

SQLALCHEMY_DATABASE_URL = "postgresql://mhduser:mhdpass@db:5432/mhd"
# add pool_pre_ping to avoid stale connections
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Result(Base):
    __tablename__ = "results"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False, index=True)
    harm_score = Column(Integer, nullable=False)
    action = Column(String, nullable=False)
    evidence = Column(JSONB, nullable=False)  # <- JSONB in Postgres
    verifier_rationale = Column(Text, nullable=True)

MAX_DB_RETRIES = int(os.environ.get("MAX_DB_RETRIES", 10))
for attempt in range(1, MAX_DB_RETRIES + 1):
    try:
        Base.metadata.create_all(bind=engine)
        break
    except OperationalError:
        wait = min(2 ** attempt, 30)
        print(f"Database not ready, retry {attempt}/{MAX_DB_RETRIES} — sleeping {wait}s")
        time.sleep(wait)
else:
    raise RuntimeError("Could not connect to the database after multiple retries")