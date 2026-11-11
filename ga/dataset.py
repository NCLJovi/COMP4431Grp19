"""Loads the labelled set and caches each message's features, so GA fitness is pure arithmetic."""
from __future__ import annotations

import csv
import json
import random
from dataclasses import dataclass

from backend.config import DATA_DIR
from backend.pipeline import detect_language, extract_features
from backend.rules import engine

SPLIT_SEED = 2027


@dataclass
class Sample:
    id: int
    text: str
    label: int
    lang: str
    category: str
    facts: frozenset[str]
    similarity: float
    url_flag: float
    rule_facts: frozenset[str]  # no URL or similarity input, used for the rule-only baseline
    ml_prob: float = 0.0


def make_sample(sample_id: int, text: str, label: int, lang: str, category: str) -> Sample:
    features = extract_features(text)
    return Sample(sample_id, text, label, lang, category,
                  frozenset(features.engine.facts), features.match.top_similarity, features.match.url_flag,
                  frozenset(engine.run(text).facts), features.classifier or 0.0)


def load_samples() -> list[Sample]:
    """The synthetic labelled set, used for the GA and for cross-validation."""
    rows = [json.loads(line) for line in (DATA_DIR / "labelled.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    return [make_sample(r["id"], r["text"], r["label"], r["lang"], r["category"]) for r in rows]


def load_real_training() -> list[Sample]:
    """Real messages set aside for training. data/real_test.csv is never read here."""
    labels = {"scam": 1, "spam": 1, "ham": 0}
    rows = []
    path = DATA_DIR / "zh_training.csv"
    if path.exists():
        with path.open(encoding="utf-8-sig", newline="") as handle:
            rows += [(labels[r["label"].strip().lower()], r["text"]) for r in csv.DictReader(handle) if r.get("text")]
    path = DATA_DIR / "en_extra_training.tsv"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            label, _, text = line.partition("\t")
            if text.strip():
                rows.append((labels[label.strip()], text))
    return [make_sample(10000 + i, text, label, detect_language(text), "real") for i, (label, text) in enumerate(rows)]


def stratified_split(samples: list[Sample], test_ratio: float = 0.3, seed: int = SPLIT_SEED) -> tuple[list[Sample], list[Sample]]:
    rng = random.Random(seed)
    train, test = [], []
    for label in (0, 1):
        group = [s for s in samples if s.label == label]
        rng.shuffle(group)
        cut = round(len(group) * test_ratio)
        test += group[:cut]
        train += group[cut:]
    return train, test


def stratified_folds(samples: list[Sample], k: int = 5, seed: int = SPLIT_SEED) -> list[list[Sample]]:
    rng = random.Random(seed)
    folds: list[list[Sample]] = [[] for _ in range(k)]
    for label in (0, 1):
        group = [s for s in samples if s.label == label]
        rng.shuffle(group)
        for i, sample in enumerate(group):
            folds[i % k].append(sample)
    return folds
