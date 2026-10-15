import csv
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal
from app.services.ingest import get_local_user, ingest_email
from app.services.types import EmailIn

counts = Counter()
with SessionLocal() as db:
    user = get_local_user(db)
    for r in csv.DictReader(open("eval/labeled_emails.csv", encoding="utf-8")):
        counts[ingest_email(db, user.id, EmailIn(r["sender"], r["subject"], r["body"]))] += 1
    db.commit()

print(dict(counts))