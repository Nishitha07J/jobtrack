from app.services.filters import looks_like_job_email
from app.services.rules import classify
from app.services.types import EmailIn


def test_applied_email_gets_status_company_and_role():
    e = EmailIn(
        "Acme Careers <no-reply@greenhouse.io>",
        "Thank you for applying to Acme",
        "We received your application for Backend Engineer.",
    )
    r = classify(e)
    assert r.status == "applied"
    assert r.company == "Acme"
    assert r.role == "Backend Engineer"


def test_rejection_is_detected():
    e = EmailIn("Umbrella <talent@myworkday.com>", "Update",
                "Unfortunately we are not moving forward with your application.")
    assert classify(e).status == "rejected"


def test_rejection_wins_over_interview_because_of_rule_order():
    e = EmailIn("X <hr@x.com>", "Update",
                "Unfortunately we will not schedule an interview.")
    assert classify(e).status == "rejected"


def test_offer_is_detected():
    e = EmailIn("X <hr@x.com>", "Good news", "We are pleased to offer you the role.")
    assert classify(e).status == "offer"


def test_unrelated_email_has_no_status():
    assert classify(EmailIn("Swiggy <offers@swiggy.in>", "50% off pizza", "")).status is None


def test_filter_rejects_pizza_and_accepts_ats_sender():
    assert not looks_like_job_email(EmailIn("Swiggy <offers@swiggy.in>", "50% off pizza", ""))
    assert looks_like_job_email(EmailIn("Acme <jobs@lever.co>", "Hello", ""))