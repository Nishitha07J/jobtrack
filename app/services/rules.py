import re

from app.services.types import EmailIn, Result

# Order matters: the first match wins.
PATTERNS = [
    ("offer", r"pleased to offer|offer letter|job offer|excited to offer"),
    ("rejected", r"unfortunately|regret to inform|not moving forward|"
                 r"other candidates|will not be proceeding|not selected"),
    ("oa", r"online assessment|coding (test|challenge|assessment)|"
           r"hackerrank|codility|take-home|assessment link"),
    ("interview", r"interview|schedule a (call|chat)|meet with (our|the) team"),
    ("applied", r"thank you for applying|thanks for applying|"
                r"application (has been )?received|received your application|"
                r"successfully submitted"),
]

COMPANY_PATTERNS = [
    r"applying (?:to|at|for a position at) ([A-Z][\w&.\-]*(?: [A-Z][\w&.\-]*){0,3})",
    r"application (?:to|at|with) ([A-Z][\w&.\-]*(?: [A-Z][\w&.\-]*){0,3})",
    r"interest in ([A-Z][\w&.\-]*(?: [A-Z][\w&.\-]*){0,3})",
]
GENERIC_WORDS = re.compile(
    r"\b(recruiting|recruitment|careers|talent|jobs|team|hr|no-?reply|hiring)\b",
    re.I,
)


def extract_company(email: EmailIn) -> str | None:
    text = f"{email.subject}\n{email.body}"
    for pat in COMPANY_PATTERNS:
        m = re.search(pat, text)
        if m:
            return m.group(1).strip()
    # Fallback: display name from the sender, e.g. "Acme Careers <x@acme.com>"
    name = email.sender.split("<")[0].strip().strip('"')
    name = GENERIC_WORDS.sub("", name).strip(" -@")
    return name or None


def classify(email: EmailIn) -> Result:
    text = f"{email.subject}\n{email.body}".lower()
    for status, pattern in PATTERNS:
        if re.search(pattern, text):
            return Result(status, extract_company(email), 0.9, "rule")
    return Result(None, None, 0.0, "rule")