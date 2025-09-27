# app/db.py (add JSON-friendly evidence)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "postgresql://mhduser:mhdpass@db:5432/mhd"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Result(Base):
    __tablename__ = "results"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False, index=True)
    harm_score = Column(Integer, nullable=False)
    action = Column(String, nullable=False)
    evidence = Column(JSONB, nullable=False)  # <- JSONB in Postgres

Base.metadata.create_all(bind=engine)
