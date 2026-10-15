import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Application

SUFFIXES = re.compile(
    r"\b(inc|llc|ltd|pvt|private|limited|corp|corporation|technologies|technology|solutions)\b\.?",
    re.I,
)
RANK = {"applied": 1, "oa": 2, "interview": 3, "offer": 4, "rejected": 5}


def normalize(text: str) -> str:
    text = SUFFIXES.sub("", text.lower())
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def find_or_create_application(
    db: Session, user_id: int, company: str, role: str = "Unknown"
) -> Application:
    company_norm, role_norm = normalize(company), normalize(role)
    app = db.scalar(
        select(Application).where(
            Application.user_id == user_id,
            Application.company_norm == company_norm,
            Application.role_norm == role_norm,
        )
    )
    if app is None:
        app = Application(
            user_id=user_id, company=company, role=role,
            company_norm=company_norm, role_norm=role_norm, status="applied",
        )
        db.add(app)
        db.flush()
    return app


def maybe_advance_status(app: Application, new_status: str) -> None:
    """Only move forward, so an old 'applied' email never undoes an 'interview'."""
    if RANK.get(new_status, 0) > RANK.get(app.status, 0):
        app.status = new_status