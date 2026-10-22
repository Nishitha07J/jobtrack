from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Application, ApplicationEvent, Email
from app.db.session import SessionLocal
from app.services.dedupe import find_or_create_application, maybe_advance_status
from app.services.ingest import get_local_user, ingest_email
from app.services.pipelines import process
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
VALID_STATUSES = {key for key, _ in COLUMNS}

MESSAGES = {
    "saved": "Saved. The card is on the board.",
    "skipped": "Not recognised as a job email, so nothing was added.",
    "needs_review": "Looks like a job email but the company is unclear. Check the Review page.",
    "duplicate": "You already added this exact email.",
}


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


@router.get("/review")
def review(request: Request, db: Session = Depends(get_db)):
    user = get_local_user(db)
    pending = db.scalars(
        select(Email)
        .where(Email.user_id == user.id, Email.classified_at.is_(None))
        .order_by(Email.received_at.desc())
    ).all()
    return templates.TemplateResponse(request, "review.html", {"pending": pending})


@router.post("/review/{email_id}")
def resolve(email_id: int, company: str = Form(...), db: Session = Depends(get_db)):
    user = get_local_user(db)
    row = db.scalar(select(Email).where(Email.id == email_id, Email.user_id == user.id))
    if row is None or row.classified_at is not None:
        raise HTTPException(status_code=404, detail="not found")
    result = process(EmailIn(row.sender, row.subject, row.snippet))
    if result.status is None:
        raise HTTPException(status_code=400, detail="could not classify")
    now = datetime.now(timezone.utc)
    app = find_or_create_application(db, user.id, company.strip(), result.role or "Unknown")
    maybe_advance_status(app, result.status)
    app.last_event_at = now
    db.add(ApplicationEvent(
        application_id=app.id, email_id=row.id, event_type=result.status,
        confidence=1.0, source="manual", needs_review=False,
    ))
    row.classified_at = now
    db.commit()
    return RedirectResponse("/review", status_code=303)