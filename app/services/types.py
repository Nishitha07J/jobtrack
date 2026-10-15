from dataclasses import dataclass


@dataclass
class EmailIn:
    sender: str
    subject: str
    body: str = ""


@dataclass
class Result:
    status: str | None      # applied | oa | interview | offer | rejected | None
    company: str | None
    confidence: float
    source: str             # rule | llm