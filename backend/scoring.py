"""Risk formula: sum(rule weight) + w_match * similarity + w_url * url_flag + w_ml * classifier probability,
clamped to 0-100."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable

from .config import HIGH_THRESHOLD, MEDIUM_THRESHOLD, TUNED_WEIGHTS_PATH
from .rules.rule_base import COMPOUND_RULES, RULES, W_MATCH_DEFAULT, W_ML_DEFAULT, W_URL_DEFAULT


@dataclass
class Weights:
    rules: dict[str, float]
    w_match: float
    w_url: float
    source: str = "hand"
    w_ml: float = 0.0


def default_weights() -> Weights:
    return Weights({r.id: r.weight for r in (*RULES, *COMPOUND_RULES)}, W_MATCH_DEFAULT, W_URL_DEFAULT, w_ml=W_ML_DEFAULT)


def load_weights() -> Weights:
    """Use GA-tuned weights when present, otherwise the hand-set ones."""
    weights = default_weights()
    if TUNED_WEIGHTS_PATH.exists():
        tuned = json.loads(TUNED_WEIGHTS_PATH.read_text(encoding="utf-8"))
        weights.rules.update({k: v for k, v in tuned["rules"].items() if k in weights.rules})
        weights.w_match = tuned["w_match"]
        weights.w_url = tuned["w_url"]
        weights.w_ml = tuned.get("w_ml", weights.w_ml)
        weights.source = "ga"
    return weights


def raw_score(facts: Iterable[str], similarity: float, url_flag: float, weights: Weights, ml_prob: float = 0.0) -> float:
    return (sum(weights.rules.get(f, 0.0) for f in facts)
            + weights.w_match * similarity
            + weights.w_url * url_flag
            + weights.w_ml * ml_prob)


def clamp_score(value: float) -> int:
    return max(0, min(100, round(value)))


def risk_level(score: int) -> str:
    if score >= HIGH_THRESHOLD:
        return "high"
    return "medium" if score >= MEDIUM_THRESHOLD else "low"


def breakdown(facts: Iterable[str], similarity: float, url_flag: float, weights: Weights, ml_prob: float = 0.0) -> dict[str, float]:
    facts = list(facts)
    return {
        "rules": round(sum(weights.rules.get(f, 0.0) for f in facts), 1),
        "similar_case": round(weights.w_match * similarity, 1),
        "url": round(weights.w_url * url_flag, 1),
        "classifier": round(weights.w_ml * ml_prob, 1),
    }
