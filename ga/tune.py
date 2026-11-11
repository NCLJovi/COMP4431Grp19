"""Genetic algorithm for the rule weights, written from scratch.

Run: python -m ga.tune

Each chromosome holds one weight per rule plus w_match and w_url. Fitness is F1 on the training split,
plus a small margin term because F1 stays flat for most small weight changes, minus a small penalty for
drifting from the hand-set weights. On a flat fitness surface weights otherwise wander and stop being
explainable. The test split is never used during tuning.

The classifier weight is set afterwards in a separate one-dimensional search. The classifier was trained
on spam rather than scams, so its signal is noisy; letting it into the GA reshuffled every rule weight.
"""
from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass, replace

from backend.config import MEDIUM_THRESHOLD, RESULTS_DIR, TUNED_WEIGHTS_PATH
from backend.scoring import Weights, clamp_score, default_weights

from .dataset import Sample, load_real_training, load_samples, stratified_split


MIN_RED_FLAG_WEIGHT = 3.0  # a rule shown to users as a red flag must still count for something
DRIFT_PENALTY = 0.03


@dataclass
class GAConfig:
    population: int = 60
    generations: int = 120
    tournament: int = 3
    crossover_rate: float = 0.8
    mutation_rate: float = 0.12
    mutation_sigma: float = 5.0
    elites: int = 2
    seed: int = 4431


def gene_names(base: Weights) -> list[str]:
    return sorted(k for k in base.rules if k != "U1") + ["w_match", "w_url"]


def bounds(name: str) -> tuple[float, float]:
    if name.startswith("M"):
        return -40.0, 0.0
    if name in ("w_match", "w_url"):
        return 0.0, 60.0
    return MIN_RED_FLAG_WEIGHT, 45.0


def to_weights(genes: list[float], names: list[str], base: Weights) -> Weights:
    values = dict(zip(names, genes))
    rules = {**base.rules, **{k: v for k, v in values.items() if k in base.rules}}
    return Weights(rules, values["w_match"], values["w_url"], "ga", base.w_ml)


def predict_score(sample: Sample, weights: Weights) -> float:
    return (sum(weights.rules.get(f, 0.0) for f in sample.facts)
            + weights.w_match * sample.similarity + weights.w_url * sample.url_flag + weights.w_ml * sample.ml_prob)


def confusion(samples: list[Sample], weights: Weights) -> dict[str, int]:
    tp = fp = fn = tn = 0
    for s in samples:
        predicted = clamp_score(predict_score(s, weights)) >= MEDIUM_THRESHOLD
        if predicted and s.label:
            tp += 1
        elif predicted:
            fp += 1
        elif s.label:
            fn += 1
        else:
            tn += 1
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn}


def f1(c: dict[str, int]) -> float:
    return 2 * c["tp"] / (2 * c["tp"] + c["fp"] + c["fn"]) if c["tp"] else 0.0


def objective(weights: Weights, samples: list[Sample]) -> float:
    # Margin rewards scores far from the threshold on the correct side, capped so it cannot outweigh F1.
    margin = sum(max(-1.0, min(1.0, (predict_score(s, weights) - MEDIUM_THRESHOLD) / 40)) * (1 if s.label else -1)
                 for s in samples) / len(samples)
    return f1(confusion(samples, weights)) + 0.02 * margin


def fitness(genes: list[float], names: list[str], base: Weights, samples: list[Sample], start: list[float]) -> float:
    drift = sum(abs(g - s) for g, s in zip(genes, start)) / (len(genes) * 50)
    return objective(to_weights(genes, names, base), samples) - DRIFT_PENALTY * drift


def no_classifier(samples: list[Sample]) -> list[Sample]:
    return [replace(s, ml_prob=0.0) for s in samples]


def with_classifier_weight(samples: list[Sample], weights: Weights) -> Weights:
    """Keeps the rule weights and picks w_ml from 0 to 40 on the given samples. 0 means the signal did not help."""
    best = max(range(41), key=lambda w: (objective(replace(weights, w_ml=float(w)), samples), -w))
    return replace(weights, w_ml=float(best))


def _tournament(rng: random.Random, population: list, scores: list[float], size: int) -> list[float]:
    best = max(rng.sample(range(len(population)), size), key=lambda i: scores[i])
    return population[best]


def evolve(samples: list[Sample], cfg: GAConfig, base: Weights | None = None) -> tuple[Weights, list[dict]]:
    base = base or default_weights()
    rng = random.Random(cfg.seed)
    names = gene_names(base)
    limits = [bounds(n) for n in names]
    start = [{"w_match": base.w_match, "w_url": base.w_url}.get(n, base.rules.get(n, 0.0)) for n in names]

    population = [list(start)]
    while len(population) < cfg.population:
        population.append([min(hi, max(lo, g + rng.gauss(0, 10))) for g, (lo, hi) in zip(start, limits)])

    history = []
    for generation in range(cfg.generations):
        scores = [fitness(p, names, base, samples, start) for p in population]
        order = sorted(range(len(population)), key=lambda i: scores[i], reverse=True)
        best = population[order[0]]
        history.append({"generation": generation, "best_fitness": round(scores[order[0]], 4),
                        "mean_fitness": round(sum(scores) / len(scores), 4),
                        "best_f1": round(f1(confusion(samples, to_weights(best, names, base))), 4)})
        next_population = [list(population[i]) for i in order[:cfg.elites]]
        while len(next_population) < cfg.population:
            a = _tournament(rng, population, scores, cfg.tournament)
            b = _tournament(rng, population, scores, cfg.tournament)
            child = [x if rng.random() < 0.5 else y for x, y in zip(a, b)] if rng.random() < cfg.crossover_rate else list(a)
            for i, (lo, hi) in enumerate(limits):
                if rng.random() < cfg.mutation_rate:
                    child[i] = min(hi, max(lo, child[i] + rng.gauss(0, cfg.mutation_sigma)))
            next_population.append(child)
        population = next_population

    scores = [fitness(p, names, base, samples, start) for p in population]
    return to_weights(max(zip(scores, population), key=lambda x: x[0])[1], names, base), history


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=GAConfig.seed)
    parser.add_argument("--generations", type=int, default=GAConfig.generations)
    args = parser.parse_args()

    samples = load_samples()
    train, _ = stratified_split(samples)
    # Real training messages join the synthetic training split. The synthetic test split and
    # data/real_test.csv are never used here.
    real = load_real_training()
    print(f"Tuning on {len(train)} synthetic and {len(real)} real messages")
    tuned, history = evolve(no_classifier(train + real), GAConfig(seed=args.seed, generations=args.generations))
    # The classifier weight is chosen on the balanced synthetic split only: the real messages are all
    # scams and almost all Chinese, which the English classifier cannot read.
    tuned = with_classifier_weight(train, tuned)
    TUNED_WEIGHTS_PATH.write_text(json.dumps(
        {"rules": {k: round(v, 2) for k, v in tuned.rules.items()},
         "w_match": round(tuned.w_match, 2), "w_url": round(tuned.w_url, 2), "w_ml": round(tuned.w_ml, 2), "seed": args.seed},
        indent=2), encoding="utf-8")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / "ga_history.json").write_text(json.dumps(history, indent=1), encoding="utf-8")
    print(f"Train F1: {history[0]['best_f1']} (generation 0 best) -> {history[-1]['best_f1']} (last generation)")
    print(f"Classifier weight w_ml: {tuned.w_ml:.1f}")
    print(f"Saved {TUNED_WEIGHTS_PATH}")


if __name__ == "__main__":
    main()
