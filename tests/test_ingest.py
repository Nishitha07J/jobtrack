from sqlalchemy import func, select

from app.db.models import Application
from app.services.ingest import get_local_user, ingest_email
from app.services.types import EmailIn

APPLIED = EmailIn(
    "Hooli Careers <jobs@lever.co>",
    "Thank you for applying to Hooli",
    "We received your application for Data Analyst.",
)


def test_same_email_twice_is_a_duplicate(db):
    user = get_local_user(db)
    assert ingest_email(db, user.id, APPLIED) == "saved"
    assert ingest_email(db, user.id, APPLIED) == "duplicate"


def test_whitespace_and_case_do_not_defeat_duplicate_detection(db):
    user = get_local_user(db)
    ingest_email(db, user.id, APPLIED)
    messy = EmailIn(
        "hooli careers <jobs@lever.co>",
        "Thank you for applying to Hooli  ",
        "We received your application for  Data Analyst.\n",
    )
    assert ingest_email(db, user.id, messy) == "duplicate"


def test_two_emails_about_one_job_make_one_card(db):
    user = get_local_user(db)
    ingest_email(db, user.id, APPLIED)
    interview = EmailIn(
        "Hooli Careers <jobs@lever.co>",
        "Interview with Hooli",
        "We would like to interview you for the Data Analyst position at Hooli.",
    )
    assert ingest_email(db, user.id, interview) == "saved"
    assert db.scalar(select(func.count()).select_from(Application)) == 1
    assert db.scalar(select(Application.status)) == "interview"


def test_non_job_email_is_skipped(db):
    user = get_local_user(db)
    assert ingest_email(db, user.id, EmailIn("Swiggy <o@swiggy.in>", "50% off pizza", "")) == "skipped"