"""Detection rate on real messages that were never used to write rules or tune weights.

Run: python -m evaluation.real_test

data/real_test.csv has the columns label, lang, category, text and source. Do not change rules after
looking at these results, otherwise the figure stops being fair.
"""
from __future__ import annotations

import asyncio
import csv
import json
from collections import Counter

from backend.config import DATA_DIR, RESULTS_DIR
from backend.service import check_message

TEST_FILE = DATA_DIR / "real_test.csv"


def main() -> None:
    with TEST_FILE.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    results = []
    for row in rows:
        answer = asyncio.run(check_message(row["text"][:2000]))
        results.append({**row, "risk_score": answer.risk_score, "risk_level": answer.risk_level,
                        "matched_patterns": answer.matched_patterns})

    scams = [r for r in results if r["label"] == "scam"]
    legit = [r for r in results if r["label"] == "ham"]
    summary = {
        "messages": len(results),
        "scam": len(scams),
        "ham": len(legit),
        "scam_flagged": sum(r["risk_level"] != "low" for r in scams),
        "scam_high": sum(r["risk_level"] == "high" for r in scams),
        "ham_flagged": sum(r["risk_level"] != "low" for r in legit),
        "levels": dict(Counter(r["risk_level"] for r in scams)),
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / "real_test.json").write_text(json.dumps({"summary": summary, "results": results}, ensure_ascii=False, indent=1), encoding="utf-8")

    if scams:
        print(f"Scam messages flagged: {summary['scam_flagged']} of {len(scams)} ({summary['scam_flagged'] / len(scams):.0%}), "
              f"high risk: {summary['scam_high']}")
    if legit:
        print(f"Normal messages wrongly flagged: {summary['ham_flagged']} of {len(legit)}")
    else:
        print("No normal messages in the test set, so false alarms cannot be measured yet.")
    for r in results:
        missed = (r["label"] == "scam") == (r["risk_level"] == "low")
        mark = "MISSED" if missed and r["label"] == "scam" else "FALSE ALARM" if missed else "ok"
        print(f"  {mark:11} {r['risk_score']:3} {r['risk_level']:6} {r['category']:10} {r['text'][:60]!r}")


if __name__ == "__main__":
    main()
