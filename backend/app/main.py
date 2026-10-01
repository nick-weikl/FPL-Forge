from fastapi import FastAPI
from sqlalchemy import text

from app.database import engine

app = FastAPI()


@app.get("/")
def root():
    return {"message": "FPL Forge API is running"}


@app.get("/db-test")
def test_database():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        return {"database": result.scalar()}