"""P1 boundary. P2 only calls match(), so P1 can replace what is behind it without touching scoring.

The current version is a basic demo: char n-gram TF-IDF matching and heuristic URL checks.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .similarity import find_similar
from .url_inspector import flag_value, inspect_urls


@dataclass
class MatchResult:
    similar_cases: list[dict] = field(default_factory=list)
    url_findings: list[dict] = field(default_factory=list)
    top_similarity: float = 0.0
    url_flag: float = 0.0  # 0 = nothing wrong, 1 = strong evidence of a fake link
    all_urls_official: bool = False


def match(text: str, expand_short_urls: bool = False) -> MatchResult:
    cases = find_similar(text)
    urls = inspect_urls(text, expand_short_urls=expand_short_urls)
    return MatchResult(
        similar_cases=cases,
        url_findings=urls,
        top_similarity=cases[0]["similarity"] if cases else 0.0,
        url_flag=max((flag_value(u["issue"]) for u in urls), default=0.0),
        all_urls_official=bool(urls) and all(u["issue"] is None and u["target"] for u in urls),
    )
