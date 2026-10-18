import csv
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.pipelines import process
from app.services.types import EmailIn

rows = list(csv.DictReader(open("eval/labeled_emails.csv", encoding="utf-8")))
tp, fp, fn = Counter(), Counter(), Counter()
correct = 0
company_total = company_ok = 0
role_total = role_ok = 0

for r in rows:
    res = process(EmailIn(r["sender"], r["subject"], r["body"]))
    pred = res.status or "other"
    true = r["label"]
    if pred == true:
        correct += 1
        tp[true] += 1
    else:
        fp[pred] += 1
        fn[true] += 1
        print(f"MISS  true={true:<9} pred={pred:<9} | {r['subject'][:60]}")
    if r["company"]:
        company_total += 1
        company_ok += (res.company or "").lower() == r["company"].lower()
    if r.get("role"):
        role_total += 1
        role_ok += (res.role or "").lower() == r["role"].lower()

print(f"\nStatus accuracy: {correct}/{len(rows)} = {correct / len(rows):.1%}")
if company_total:
    print(f"Company extraction: {company_ok}/{company_total} = {company_ok / company_total:.1%}")
if role_total:
    print(f"Role extraction: {role_ok}/{role_total} = {role_ok / role_total:.1%}")
print(f"\n{'label':<10}{'precision':>10}{'recall':>10}")
for label in ["applied", "oa", "interview", "offer", "rejected", "other"]:
    p = tp[label] / (tp[label] + fp[label]) if tp[label] + fp[label] else 0
    r_ = tp[label] / (tp[label] + fn[label]) if tp[label] + fn[label] else 0
    print(f"{label:<10}{p:>10.2f}{r_:>10.2f}")