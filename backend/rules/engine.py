"""Forward-chaining inference.

Step 1 turns text patterns into base facts and records where each one matched.
Step 2 applies compound rules repeatedly until no new fact appears, so one conclusion can
trigger another (R6 + R21 -> C2, then C2 + R5 -> C8).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

from ..normalize import to_traditional
from .rule_base import COMPOUND_RULES, RULES, CompoundRule, Rule

_COMPILED: dict[str, list[re.Pattern]] = {
    # Text is converted to Traditional Chinese before matching, so the patterns are converted the same way.
    r.id: [re.compile(to_traditional(p), re.IGNORECASE) for p in r.patterns] for r in RULES
}
RULES_BY_ID: dict[str, Rule | CompoundRule] = {r.id: r for r in (*RULES, *COMPOUND_RULES)}

_NEGATION = re.compile(to_traditional(r"(?:\b(?:never|not|don't|do not|won't|will not|cannot)\b|請勿|请勿|切勿|不要|唔好|不會|不会|絕不|绝不|毋須)"), re.IGNORECASE)
_CLAUSE_BREAK = re.compile(r"[.!?,;:\n。！？，；：]")
_NEGATION_WINDOW = 24


@dataclass(frozen=True)
class Hit:
    rule_id: str
    span: tuple[int, int] | None


@dataclass
class EngineResult:
    facts: set[str] = field(default_factory=set)
    hits: list[Hit] = field(default_factory=list)
    trace: list[str] = field(default_factory=list)


def _is_negated(text: str, start: int) -> bool:
    """True when a negation sits before the match inside the same clause."""
    before = text[max(0, start - _NEGATION_WINDOW):start]
    clause = _CLAUSE_BREAK.split(before)[-1]
    return bool(_NEGATION.search(clause))


def _merge_spans(spans: list[tuple[int, int]]) -> list[tuple[int, int]]:
    merged: list[tuple[int, int]] = []
    for start, end in sorted(spans):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def match_base_rules(text: str) -> EngineResult:
    result = EngineResult()
    for rule in RULES:
        spans = []
        for pattern in _COMPILED[rule.id]:
            for m in pattern.finditer(text):
                if m.end() > m.start() and not (rule.negatable and _is_negated(text, m.start())):
                    spans.append(m.span())
        if spans:
            result.facts.add(rule.id)
            result.hits.extend(Hit(rule.id, s) for s in _merge_spans(spans))
    return result


def forward_chain(facts: set[str]) -> tuple[list[str], list[str]]:
    """Fire compound rules until a fixed point. Returns (fired rule ids, readable trace)."""
    fired: list[str] = []
    trace: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in COMPOUND_RULES:
            if rule.id in facts:
                continue
            matched = [sorted(group & facts) for group in rule.requires]
            if all(matched):
                facts.add(rule.id)
                fired.append(rule.id)
                reasons = " + ".join(m[0] if len(m) == 1 else "(" + "|".join(m) + ")" for m in matched)
                trace.append(f"{reasons} -> {rule.id} {rule.name}")
                changed = True
    return fired, trace


def run(text: str, external_facts: Iterable[str] = ()) -> EngineResult:
    """`external_facts` lets other modules add facts, e.g. U1 from the URL inspector."""
    result = match_base_rules(text)
    for fact in external_facts:
        if fact not in result.facts:
            result.facts.add(fact)
            result.hits.append(Hit(fact, None))
    fired, result.trace = forward_chain(result.facts)
    result.hits.extend(Hit(rule_id, None) for rule_id in fired)
    return result
