from app.services.filters import looks_like_job_email
from app.services.rules import classify
from app.services.types import EmailIn, Result


def process(email: EmailIn) -> Result:
    if not looks_like_job_email(email):
        return Result(None, None, 1.0, "rule")
    return classify(email)   # the LLM fallback plugs in here later