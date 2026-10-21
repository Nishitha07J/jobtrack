from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Application, ApplicationEvent
from app.db.session import SessionLocal
from app.services.ingest import get_local_user, ingest_email
from app.services.types import EmailIn

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

VALID_STATUSES = {key for key, _ in COLUMNS}


@router.post("/applications/{app_id}/status")
def set_status(app_id: int, payload: dict, db: Session = Depends(get_db)):
    status = payload.get("status")
    if status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail="invalid status")
    user = get_local_user(db)
    app = db.scalar(
        select(Application).where(
            Application.id == app_id, Application.user_id == user.id
        )
    )
    if app is None:
        raise HTTPException(status_code=404, detail="not found")
    app.status = status
    db.add(ApplicationEvent(
        application_id=app.id, event_type=status,
        confidence=1.0, source="manual", needs_review=False,
    ))
    db.commit()
    return {"ok": True}

MESSAGES = {
    "saved": "Saved. The card is on the board.",
    "skipped": "Not recognised as a job email, so nothing was added.",
    "needs_review": "Status found but no company name, so it was not added.",
    "duplicate": "You already added this exact email.",
}


@router.get("/add")
def add_form(request: Request, result: str | None = None):
    return templates.TemplateResponse(
        request, "add.html", {"message": MESSAGES.get(result or "")}
    )


@router.post("/add")
def add_email(
    sender: str = Form(""),
    subject: str = Form(...),
    body: str = Form(""),
    db: Session = Depends(get_db),
):
    user = get_local_user(db)
    result = ingest_email(db, user.id, EmailIn(sender, subject, body))
    db.commit()
    return RedirectResponse(f"/add?result={result}", status_code=303)