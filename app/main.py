from fastapi import FastAPI
from sqlalchemy import text

from app.db.session import engine

app = FastAPI(title="JobTrack")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/db-check")
def db_check():
    with engine.connect() as conn:
        return {"db": conn.execute(text("select 1")).scalar()}