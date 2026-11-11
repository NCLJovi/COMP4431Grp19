"""Evaluation: rule-only, classifier-only, hybrid variants and optional LLM-only, plus latency and error analysis.

Run: python -m evaluation.run_eval          (add --llm when Ollama is running)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import time
from dataclasses import replace

from backend import llm
from backend.config import MEDIUM_THRESHOLD, RESULTS_DIR
from backend.pipeline import analyze, extract_features
from backend.scoring import Weights, clamp_score, default_weights, load_weights
from ga.dataset import Sample, load_samples, stratified_folds, stratified_split
from ga.tune import GAConfig, confusion, evolve, f1, no_classifier, predict_score, with_classifier_weight

DATA_WARNING = ("The labelled set is synthetic and was written by the same author as the rules, so these figures "
                "show the method working and do not estimate real-world accuracy. Replace it with real data (P1).")


def metrics(c: dict[str, int]) -> dict[str, float]:
    total = sum(c.values())
    return {**c, "accuracy": round((c["tp"] + c["tn"]) / total, 3),
            "precision": round(c["tp"] / (c["tp"] + c["fp"]), 3) if c["tp"] + c["fp"] else 0.0,
            "recall": round(c["tp"] / (c["tp"] + c["fn"]), 3) if c["tp"] + c["fn"] else 0.0,
            "f1": round(f1(c), 3)}


def rule_only_view(samples: list[Sample]) -> list[Sample]:
    return [replace(s, facts=s.rule_facts, similarity=0.0, url_flag=0.0, ml_prob=0.0) for s in samples]


def classifier_only(samples: list[Sample]) -> dict[str, int]:
    """The trained models alone at the 0.5 threshold. Without a Chinese model, Chinese messages are never flagged."""
    c = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    for s in samples:
        c[("tp" if s.label else "fp") if s.ml_prob >= 0.5 else ("fn" if s.label else "tn")] += 1
    return c


def english(samples: list[Sample]) -> list[Sample]:
    return [s for s in samples if s.lang == "en"]


def add(a: dict[str, int], b: dict[str, int]) -> dict[str, int]:
    return {k: a.get(k, 0) + v for k, v in b.items()}


def cross_validate(samples: list[Sample], cfg: GAConfig) -> dict:
    """Out-of-fold results: each fold is scored by weights tuned on the other four."""
    hand = default_weights()
    folds = stratified_folds(samples)
    total = {"rule_only": {}, "classifier_only": {}, "classifier_only_english": {}, "hybrid": {}, "hybrid_ga": {}, "hybrid_ga_classifier": {}}
    errors = []
    for i, fold in enumerate(folds):
        train = [s for j, other in enumerate(folds) if j != i for s in other]
        tuned_plain, _ = evolve(no_classifier(train), cfg, hand)
        tuned = with_classifier_weight(train, tuned_plain)
        total["rule_only"] = add(total["rule_only"], confusion(rule_only_view(fold), hand))
        total["classifier_only"] = add(total["classifier_only"], classifier_only(fold))
        total["classifier_only_english"] = add(total["classifier_only_english"], classifier_only(english(fold)))
        total["hybrid"] = add(total["hybrid"], confusion(no_classifier(fold), hand))
        total["hybrid_ga"] = add(total["hybrid_ga"], confusion(no_classifier(fold), tuned_plain))
        total["hybrid_ga_classifier"] = add(total["hybrid_ga_classifier"], confusion(fold, tuned))
        for s in fold:
            score = clamp_score(predict_score(s, tuned))
            if (score >= MEDIUM_THRESHOLD) != bool(s.label):
                errors.append({"id": s.id, "type": "FP" if not s.label else "FN", "score": score, "lang": s.lang,
                               "category": s.category, "text": s.text, "rules": sorted(s.facts)})
    return {"summary": {k: metrics(v) for k, v in total.items()}, "errors": sorted(errors, key=lambda e: e["id"])}


def by_language(samples: list[Sample], weights: Weights) -> dict:
    return {lang: metrics(confusion([s for s in samples if s.lang == lang], weights)) for lang in ("en", "zh")}


def latency(samples: list[Sample]) -> dict:
    timings = []
    for s in samples:
        start = time.perf_counter()
        asyncio.run(analyze(s.text, use_llm=False))
        timings.append((time.perf_counter() - start) * 1000)
    timings.sort()
    return {"n": len(timings), "p50_ms": round(statistics.median(timings), 2), "p95_ms": round(timings[int(len(timings) * 0.95) - 1], 2)}


async def llm_only(samples: list[Sample]) -> dict:
    c = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    timings, failed = [], 0
    for s in samples:
        start = time.perf_counter()
        scam = await llm.classify(s.text)
        timings.append(time.perf_counter() - start)
        if scam is None:
            failed += 1
            scam = False  # no answer gives no protection, so it counts as "not flagged"
        c[("tp" if s.label else "fp") if scam else ("fn" if s.label else "tn")] += 1
    return {**metrics(c), "failed_calls": failed, "mean_seconds": round(statistics.mean(timings), 2)}


def write_report(result: dict) -> None:
    lines = ["# Evaluation results", "", f"> **Caution:** {DATA_WARNING}", "",
             f"Dataset: {result['dataset']['total']} messages ({result['dataset']['scam']} scam, {result['dataset']['legit']} legitimate). Scam means score >= {MEDIUM_THRESHOLD}.", "",
             "## Held-out test set (GA never saw it)", "", "| Method | Accuracy | Precision | Recall | F1 |", "|---|---|---|---|---|"]
    rows = lambda table: [f"| {name} | {m['accuracy']} | {m['precision']} | {m['recall']} | {m['f1']} |" for name, m in table.items()]
    lines += rows(result["test"])
    lines += ["", "## 5-fold cross-validation (out-of-fold)", "", "| Method | Accuracy | Precision | Recall | F1 |", "|---|---|---|---|---|"]
    lines += rows(result["cross_validation"]["summary"])
    lines += ["", "## By language, final model on all messages (includes training data)", "", "| Language | Accuracy | Precision | Recall | F1 |", "|---|---|---|---|---|"]
    lines += rows(result["by_language"])
    lat = result["latency"]
    lines += ["", "## Response time, without the LLM", "", f"p50 {lat['p50_ms']} ms, p95 {lat['p95_ms']} ms over {lat['n']} messages.", "",
              "## Out-of-fold errors", "", "| ID | Type | Score | Lang | Category | Message |", "|---|---|---|---|---|---|"]
    for e in result["cross_validation"]["errors"]:
        text = e["text"].replace("|", "/")
        lines.append(f"| {e['id']} | {e['type']} | {e['score']} | {e['lang']} | {e['category']} | {text} |")
    (RESULTS_DIR / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--llm", action="store_true", help="also run the LLM-only baseline (needs Ollama)")
    args = parser.parse_args()

    samples = load_samples()
    _, test = stratified_split(samples)
    hand, tuned = default_weights(), load_weights()
    if tuned.source != "ga":
        raise SystemExit("No tuned weights found. Run: python -m ga.tune")

    table = {"rule_only": metrics(confusion(rule_only_view(test), hand)),
             "classifier_only": metrics(classifier_only(test)),
             "classifier_only_english": metrics(classifier_only(english(test))),
             "hybrid": metrics(confusion(no_classifier(test), hand)),
             "hybrid_ga": metrics(confusion(no_classifier(test), tuned)),
             "hybrid_ga_classifier": metrics(confusion(test, tuned))}
    if args.llm:
        table["llm_only"] = asyncio.run(llm_only(test))

    result = {
        "warning": DATA_WARNING,
        "dataset": {"total": len(samples), "scam": sum(s.label for s in samples), "legit": sum(1 - s.label for s in samples)},
        "test": table,
        "cross_validation": cross_validate(samples, GAConfig()),
        "by_language": by_language(samples, tuned),
        "latency": latency(samples),
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / "metrics.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    write_report(result)
    print(f"CAUTION: {DATA_WARNING}\n")
    for title, rows in (("Held-out test", table), ("5-fold CV", result["cross_validation"]["summary"])):
        print(title)
        for name, m in rows.items():
            print(f"  {name:<24} acc={m['accuracy']:<6} prec={m['precision']:<6} recall={m['recall']:<6} f1={m['f1']}")
    print(f"Latency without LLM: p50={result['latency']['p50_ms']}ms p95={result['latency']['p95_ms']}ms")
    print(f"Out-of-fold errors: {len(result['cross_validation']['errors'])}. Report: {RESULTS_DIR / 'report.md'}")


if __name__ == "__main__":
    main()
