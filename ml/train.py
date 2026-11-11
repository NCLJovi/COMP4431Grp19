"""Train a TF-IDF + logistic regression classifier for English or Chinese.

English, on the SMS Spam Collection:   python -m ml.train
English, with your own messages:       python -m ml.train --extra my_messages.tsv
Chinese, on data/zh_training.csv:      python -m ml.train --language zh

Exact duplicates are removed before any split, otherwise the same message could sit in both train and test.
Messages in data/labelled.jsonl are left out too, because that file is the test set.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.pipeline import Pipeline

from backend.config import CLASSIFIER_PATH, DATA_DIR, RESULTS_DIR, ZH_CLASSIFIER_PATH
from backend.normalize import normalize

SEED = 4431
CORPUS = DATA_DIR / "sms_spam" / "SMSSpamCollection"
ZH_CORPUS = DATA_DIR / "zh_training.csv"
MIN_PER_CLASS = 20
ZH_LABELS = {"scam": 1, "spam": 1, "ham": 0}


def _key(text: str) -> str:
    return " ".join(normalize(text)[0].lower().split())


def _test_set_keys() -> set[str]:
    rows = (DATA_DIR / "labelled.jsonl").read_text(encoding="utf-8").splitlines()
    return {_key(json.loads(row)["text"]) for row in rows if row.strip()}


def deduplicate(rows: list[tuple[int, str]]) -> dict:
    """Takes (label, text) pairs and drops duplicates and anything that is in the test set."""
    test_set = _test_set_keys()
    seen: set[str] = set()
    data = {"texts": [], "labels": [], "duplicates": 0, "in_test_set": 0}
    for label, text in rows:
        # The app cleans text the same way before the model sees it.
        text = normalize(text)[0]
        key = _key(text)
        if key in test_set:
            data["in_test_set"] += 1
        elif key in seen:
            data["duplicates"] += 1
        else:
            seen.add(key)
            data["texts"].append(text)
            data["labels"].append(label)
    return data


def load_english(extra: Path | None = None) -> list[tuple[int, str]]:
    """Reads the corpus, plus an optional extra file in the same tab-separated format."""
    lines = CORPUS.read_text(encoding="utf-8").splitlines()
    corpus_size = len(lines)
    if extra:
        lines += [line for line in extra.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    rows = []
    for number, line in enumerate(lines, 1):
        label, _, text = line.partition("\t")
        if label not in ("ham", "spam") or not text.strip():
            raise SystemExit(f"Bad line {number - corpus_size} in {extra}: expected ham or spam, a tab, then the message. Got: {line[:60]}")
        rows.append((1 if label == "spam" else 0, text))
    return rows


def load_chinese(path: Path = ZH_CORPUS) -> list[tuple[int, str]]:
    """Reads a CSV with the columns label and text. Any other column, such as source, is ignored."""
    rows = []
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if not {"label", "text"} <= set(reader.fieldnames or []):
                raise SystemExit(f"{path} needs the columns label and text. Found: {reader.fieldnames}")
            for row in reader:
                label, text = (row["label"] or "").strip().lower(), (row["text"] or "").strip()
                if not label and not text:
                    continue
                if label not in ZH_LABELS or not text:
                    raise SystemExit(f"Bad row {reader.line_num} in {path}: label must be scam or ham, and text must not be empty.")
                rows.append((ZH_LABELS[label], text))
    except UnicodeDecodeError:
        raise SystemExit(f"{path} is not UTF-8. In Excel, use Save As and choose CSV UTF-8.") from None
    return rows


def build_model(language: str = "en") -> Pipeline:
    if language == "zh":
        # Chinese has no spaces between words, so the features are runs of 1 to 3 characters.
        vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(1, 3), sublinear_tf=True, min_df=2)
    else:
        vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 2), sublinear_tf=True, min_df=2)
    return Pipeline([
        ("tfidf", vectorizer),
        ("lr", LogisticRegression(C=10.0, class_weight="balanced", max_iter=2000)),
    ])


def scores(truth: list[int], predicted) -> dict[str, float]:
    return {"accuracy": round(accuracy_score(truth, predicted), 4),
            "precision": round(precision_score(truth, predicted), 4),
            "recall": round(recall_score(truth, predicted), 4),
            "f1": round(f1_score(truth, predicted), 4)}


def top_terms(model: Pipeline, n: int = 15) -> dict[str, list[str]]:
    """The terms the model relies on most, for explaining it on a slide."""
    names = model.named_steps["tfidf"].get_feature_names_out()
    order = model.named_steps["lr"].coef_[0].argsort()
    return {"spam": [str(names[i]) for i in order[::-1][:n]], "ham": [str(names[i]) for i in order[:n]]}


def train(data: dict, language: str, model_path: Path) -> dict:
    texts, labels = data["texts"], data["labels"]
    x_train, x_test, y_train, y_test = train_test_split(texts, labels, test_size=0.2, stratify=labels, random_state=SEED)

    held_out = build_model(language).fit(x_train, y_train)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    cv_predicted = cross_val_predict(build_model(language), texts, labels, cv=cv)

    # The figures above come from held-back data; the saved model then uses every message.
    final = build_model(language).fit(texts, labels)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(final, model_path, compress=3)

    return {
        "messages": len(texts), "spam": sum(labels), "ham": len(labels) - sum(labels),
        "duplicates_removed": data["duplicates"], "removed_because_in_test_set": data["in_test_set"],
        "majority_class_accuracy": round(max(sum(labels), len(labels) - sum(labels)) / len(labels), 4),
        "held_out_20_percent": scores(y_test, held_out.predict(x_test)),
        "cv_5_fold": scores(labels, cv_predicted),
        "vocabulary_size": len(final.named_steps["tfidf"].vocabulary_),
        "top_terms": top_terms(final),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--language", choices=("en", "zh"), default="en")
    parser.add_argument("--extra", type=Path, help="English only. Extra messages: ham or spam, a tab, then the message")
    args = parser.parse_args()
    if args.language == "zh" and args.extra:
        parser.error("--extra is for English. Chinese data goes in data/zh_training.csv")

    chinese = args.language == "zh"
    data = deduplicate(load_chinese() if chinese else load_english(args.extra))
    spam = sum(data["labels"])
    ham = len(data["labels"]) - spam
    if min(spam, ham) < MIN_PER_CLASS:
        raise SystemExit(f"Not enough data: found {spam} scam and {ham} ham. Each needs at least {MIN_PER_CLASS}.")

    model_path = ZH_CLASSIFIER_PATH if chinese else CLASSIFIER_PATH
    result = train(data, args.language, model_path)
    result["dataset"] = str(ZH_CORPUS.name) if chinese else "SMS Spam Collection v.1"
    result["extra_file"] = str(args.extra) if args.extra else None
    result["note"] = "Measured on this training data only. This does not measure real-world scam detection."
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / f"classifier_metrics{'_zh' if chinese else ''}.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"Messages: {result['messages']} ({spam} spam), {data['duplicates']} duplicates removed, {data['in_test_set']} removed because they are in the test set")
    print(f"Majority-class accuracy: {result['majority_class_accuracy']}")
    print(f"Held-out 20%: {result['held_out_20_percent']}")
    print(f"5-fold CV:    {result['cv_5_fold']}")
    print(f"Top spam terms: {', '.join(result['top_terms']['spam'])}")
    print(f"Saved {model_path} ({model_path.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
