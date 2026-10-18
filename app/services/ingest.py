import hashlib
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Application, ApplicationEvent, Email, User
from app.services.dedupe import find_or_create_application, maybe_advance_status
from app.services.pipelines import process
from app.services.types import EmailIn


def get_local_user(db: Session) -> User:
    user = db.scalar(select(User).where(User.google_sub == "local"))
    if user is None:
        user = User(email="local@jobtrack.dev", google_sub="local")
        db.add(user)
        db.flush()
    return user


def ingest_email(db: Session, user_id: int, email: EmailIn) -> str:
    msg_id = hashlib.sha1(
        f"{email.sender}|{email.subject}|{email.body}".encode()
    ).hexdigest()

    # Idempotency: the same email is never processed twice.
    exists = db.scalar(
        select(Email.id).where(
            Email.user_id == user_id, Email.gmail_message_id == msg_id
        )
    )
    if exists:
        return "duplicate"

    now = datetime.now(timezone.utc)
    row = Email(
        user_id=user_id, gmail_message_id=msg_id, thread_id=msg_id,
        sender=email.sender, subject=email.subject, received_at=now,
        snippet=email.body[:200], classified_at=now,
    )
    db.add(row)
    db.flush()

    result = process(email)
    if result.status is None:
        return "skipped"          # not a job email
    if not result.company:
        return "needs_review"     # status known, company unknown

    app = find_or_create_application(db, user_id, result.company, result.role or "Unknown")
    maybe_advance_status(app, result.status)
    app.last_event_at = now
    db.add(ApplicationEvent(
        application_id=app.id, email_id=row.id, event_type=result.status,
        confidence=result.confidence, source=result.source,
        needs_review=result.confidence < 0.7,
    ))
    return "saved"