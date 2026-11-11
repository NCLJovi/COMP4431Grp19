"""Single-message analysis: rule engine + P1 matching + scoring + explanation."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import classifier, llm, wording
from .config import EXPAND_SHORT_URLS
from .matching import MatchResult, match
from .normalize import normalize, original_span
from .patterns import matched_patterns
from .rules import engine
from .rules.engine import RULES_BY_ID, EngineResult
from .rules.rule_base import CompoundRule
from .schemas import AnalyzeResponse, TriggeredRule
from .scoring import Weights, breakdown, clamp_score, load_weights, raw_score, risk_level

_CJK = re.compile(r"[一-鿿]")
_LATIN = re.compile(r"[A-Za-z]")
_WEIGHTS = load_weights()


@dataclass
class Features:
    """Everything the score depends on, cached by the GA and the evaluation."""
    engine: EngineResult
    match: MatchResult
    classifier: float | None = None
    clean_text: str = ""
    origin: list[int] = field(default_factory=list)


def detect_language(text: str) -> str:
    return "zh" if len(_CJK.findall(text)) * 3 >= len(_LATIN.findall(text)) and _CJK.search(text) else "en"


def extract_features(text: str, expand_short_urls: bool = False) -> Features:
    text, origin = normalize(text)
    matched = match(text, expand_short_urls=expand_short_urls)
    external = []
    if matched.url_flag > 0:
        external.append("U1")
    if matched.all_urls_official:
        external.append("M3")
    return Features(engine.run(text, external), matched, classifier.scam_probability(text, detect_language(text)), text, origin)


def _triggered(result: EngineResult, weights: Weights, lang: str) -> list[TriggeredRule]:
    rules = []
    for hit in result.hits:
        rule = RULES_BY_ID[hit.rule_id]
        rules.append(TriggeredRule(
            id=rule.id, name=rule.name, name_zh=rule.name_zh, category=rule.category,
            span=list(hit.span) if hit.span else None, weight=round(weights.rules.get(rule.id, 0.0), 1),
            why=rule.why_zh if lang == "zh" else rule.why_en,
        ))
    return rules


def _url_sentence(finding: dict, lang: str) -> str:
    target = finding.get("target") or wording.URL_UNKNOWN_TARGET[lang]
    problem = wording.URL_PROBLEM[finding["issue"]][lang].format(target=target)
    return wording.URL_SENTENCE[lang].format(url=finding["url"], problem=problem)


def template_explanation(level: str, rules: list[TriggeredRule], urls: list[dict], cases: list[dict], lang: str) -> str:
    seen, reasons = set(), []
    ranked = sorted(rules, key=lambda r: (isinstance(RULES_BY_ID[r.id], CompoundRule), -r.weight))
    for rule in ranked:
        if rule.id not in seen and rule.weight > 0 and rule.id != "U1":
            seen.add(rule.id)
            reasons.append(rule.why)
    parts = [wording.RISK_OPENING[lang][level], *[_url_sentence(u, lang) for u in urls if u["issue"]][:2], *reasons[:3]]
    if cases and level != "low":
        title = cases[0]["title_zh" if lang == "zh" else "title"]
        parts.append(wording.SIMILAR_CASE[lang].format(title=title, similarity=cases[0]["similarity"]))
    return " ".join(parts)


async def analyze(text: str, use_llm: bool = True, weights: Weights | None = None) -> AnalyzeResponse:
    weights = weights or _WEIGHTS
    features = extract_features(text, EXPAND_SHORT_URLS)
    lang = detect_language(features.clean_text)
    result, matched = features.engine, features.match
    ml_prob = features.classifier or 0.0
    score = clamp_score(raw_score(result.facts, matched.top_similarity, matched.url_flag, weights, ml_prob))
    level = risk_level(score)
    rules = _triggered(result, weights, lang)
    # Pattern names read the matched words, so they use the cleaned text and its spans.
    patterns = matched_patterns(rules, features.clean_text, level)
    rules = [r.model_copy(update={"span": original_span(r.span, features.origin)}) for r in rules]
    url_findings = [{**u, "span": original_span(u.get("span"), features.origin)} for u in matched.url_findings]
    explanation = template_explanation(level, rules, url_findings, matched.similar_cases, lang)
    source = "template"
    if use_llm:
        facts = {
            "risk_score": score, "risk_level": level,
            "reasons": sorted({r.name for r in rules if r.weight > 0}),
            "url_problems": [{"url": u["url"], "issue": u["issue"], "imitates": u.get("target")} for u in matched.url_findings if u["issue"]],
            "similar_case": matched.similar_cases[0]["title"] if matched.similar_cases else None,
        }
        generated = await llm.explain(text, facts, lang)
        if generated:
            explanation, source = generated, "llm"
    return AnalyzeResponse(
        risk_score=score, risk_level=level, triggered_rules=rules,
        url_findings=url_findings, similar_cases=matched.similar_cases,
        explanation=explanation, explanation_source=source, language=lang,
        matched_patterns=patterns,
        inference_trace=result.trace,
        score_breakdown=breakdown(result.facts, matched.top_similarity, matched.url_flag, weights, ml_prob),
        scam_probability=None if features.classifier is None else round(features.classifier, 3),
    )
