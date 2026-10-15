from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Application
from app.db.session import SessionLocal
from app.services.ingest import get_local_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

COLUMNS = [
    ("applied", "Applied"),
    ("oa", "Online assessment"),
    ("interview", "Interview"),
    ("offer", "Offer"),
    ("rejected", "Rejected"),
]


def get_db():
    with SessionLocal() as db:
        yield db


@router.get("/")
def board(request: Request, db: Session = Depends(get_db)):
    user = get_local_user(db)
    apps = db.scalars(
        select(Application)
        .where(Application.user_id == user.id)
        .order_by(Application.last_event_at.desc().nullslast())
    ).all()
    grouped = {key: [a for a in apps if a.status == key] for key, _ in COLUMNS}
    return templates.TemplateResponse(
        request, "board.html",
        {"columns": COLUMNS, "grouped": grouped, "total": len(apps)},
    )