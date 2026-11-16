"""Every figure on real messages that the README and the slides quote.

Run: python -m evaluation.real_test

Part 1, the fair test: data/real_test.csv, real scams that were never used to write rules or tune weights.
It has the columns label, lang, category, text and source. Do not change rules after looking at these
results, otherwise the figure stops being fair.

Part 2, indicative only: real messages in data/zh_training.csv and data/en_extra_training.tsv. They were
used to write rules and tune the GA, so a good score there shows the gaps were closed, not accuracy.

A message counts as flagged at medium or high risk (score 40 or more). The full results are saved to
evaluation/results/real_test.json.

Figures measured before the rules were changed (for example 16 of 35 unseen scams) cannot be reproduced
with the current code. They are recorded in evaluation/HISTORY.md.
"""
from __future__ import annotations

import asyncio
import csv
import json
from collections import Counter

from backend.config import DATA_DIR, RESULTS_DIR
from backend.service import check_message

TEST_FILE = DATA_DIR / "real_test.csv"
ZH_TRAINING = DATA_DIR / "zh_training.csv"
EN_TRAINING = DATA_DIR / "en_extra_training.tsv"
SECOND_BATCH = "23-41"          # in the source column of the questionnaire rows added later
TEAM_COLLECTED = "組員收集"      # source of the six Chinese scams the team collected first


def score(row: dict) -> dict:
    answer = asyncio.run(check_message(row["text"][:2000]))
    return {**row, "risk_score": answer.risk_score, "risk_level": answer.risk_level,
            "matched_patterns": answer.matched_patterns}


def flagged(rows: list[dict]) -> int:
    return sum(r["risk_level"] != "low" for r in rows)


def ratio(part: int, whole: int) -> str:
    return f"{part} of {whole} ({part / whole:.0%})" if whole else "none"


def read_test_set() -> list[dict]:
    with TEST_FILE.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_training_set() -> list[dict]:
    rows = []
    if ZH_TRAINING.exists():
        with ZH_TRAINING.open(encoding="utf-8-sig", newline="") as handle:
            rows += [{"label": r["label"].strip().lower(), "lang": "zh", "text": r["text"], "source": r["source"]}
                     for r in csv.DictReader(handle) if r.get("text")]
    if EN_TRAINING.exists():
        for line in EN_TRAINING.read_text(encoding="utf-8-sig").splitlines():
            label, _, text = line.partition("\t")
            if text.strip():
                label = "scam" if label.strip().lower() == "spam" else label.strip().lower()
                rows.append({"label": label, "lang": "en", "text": text.strip(), "source": "en_extra_training.tsv"})
    return rows


def show(rows: list[dict]) -> None:
    for r in rows:
        wrong = (r["label"] == "scam") == (r["risk_level"] == "low")
        mark = ("MISSED" if r["label"] == "scam" else "FALSE ALARM") if wrong else "ok"
        print(f"  {mark:11} {r['risk_score']:3} {r['risk_level']:6} {r.get('category', ''):10} {r['text'][:60]!r}")


def main() -> None:
    test = [score(row) for row in read_test_set()]
    scams = [r for r in test if r["label"] == "scam"]
    legit = [r for r in test if r["label"] == "ham"]
    first = [r for r in scams if SECOND_BATCH not in r["source"]]
    second = [r for r in scams if SECOND_BATCH in r["source"]]

    training = [score(row) for row in read_training_set()]
    train_ham = [r for r in training if r["label"] == "ham"]
    train_scam = [r for r in training if r["label"] == "scam"]
    team_six = [r for r in train_scam if r["source"].startswith(TEAM_COLLECTED)]

    summary = {
        "messages": len(test),
        "scam": len(scams),
        "ham": len(legit),
        "scam_flagged": flagged(scams),
        "scam_high": sum(r["risk_level"] == "high" for r in scams),
        "ham_flagged": flagged(legit),
        "levels": dict(Counter(r["risk_level"] for r in scams)),
        "first_batch": {"scam": len(first), "scam_flagged": flagged(first)},
        "second_batch": {"scam": len(second), "scam_flagged": flagged(second)},
        "training_indicative": {
            "ham": len(train_ham), "ham_flagged": flagged(train_ham),
            "scam": len(train_scam), "scam_flagged": flagged(train_scam),
            "team_collected_zh": len(team_six), "team_collected_zh_flagged": flagged(team_six),
        },
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / "real_test.json").write_text(
        json.dumps({"summary": summary, "results": test, "training_results": training}, ensure_ascii=False, indent=1),
        encoding="utf-8")

    print("== Held-out test set (data/real_test.csv), never used to write rules or tune weights")
    print(f"Scam messages flagged: {ratio(flagged(scams), len(scams))}, high risk: {summary['scam_high']}")
    print(f"  first questionnaire batch:  {ratio(flagged(first), len(first))}")
    print(f"  second questionnaire batch: {ratio(flagged(second), len(second))}")
    if legit:
        print(f"Normal messages wrongly flagged: {flagged(legit)} of {len(legit)}")
    else:
        print("No normal messages in the test set, so false alarms cannot be measured on it.")
    show(test)

    print()
    print("== Real training messages (indicative only: rules and weights were tuned on them)")
    print(f"Normal messages wrongly flagged: {flagged(train_ham)} of {len(train_ham)}")
    print(f"Scam messages flagged: {ratio(flagged(train_scam), len(train_scam))}")
    print(f"  six Chinese scams collected by the team: {ratio(flagged(team_six), len(team_six))}")
    show([r for r in train_ham if r["risk_level"] != "low"] + [r for r in train_scam if r["risk_level"] == "low"])


if __name__ == "__main__":
    main()
