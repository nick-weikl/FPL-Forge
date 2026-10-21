import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is required; configure backend/.env or the environment")

engine_options = {"pool_pre_ping": True, "pool_recycle": 300}
if DATABASE_URL.startswith(("postgresql://", "postgresql+psycopg2://")):
    engine_options.update(
        pool_size=5, max_overflow=5, pool_timeout=10, connect_args={"connect_timeout": 10}
    )
engine = create_engine(DATABASE_URL, **engine_options)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
