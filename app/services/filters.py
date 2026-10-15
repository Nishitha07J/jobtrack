from app.services.types import EmailIn

ATS_DOMAINS = (
    "greenhouse.io", "lever.co", "myworkday.com", "workday.com", "ashbyhq.com",
    "smartrecruiters.com", "icims.com", "jobvite.com", "hackerrank.com",
    "codility.com", "naukri.com", "linkedin.com", "wellfound.com",
)
KEYWORDS = (
    "application", "applying", "interview", "assessment", "offer",
    "candidate", "hiring", "position", "recruit",
)


def looks_like_job_email(email: EmailIn) -> bool:
    sender = email.sender.lower()
    text = f"{email.subject} {email.body}".lower()
    return any(d in sender for d in ATS_DOMAINS) or any(k in text for k in KEYWORDS)