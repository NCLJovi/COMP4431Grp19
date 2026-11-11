"""Basic similar-case search with TF-IDF over character n-grams, which works for English and Chinese
without a word segmenter. P1 can swap this for ChromaDB/FAISS + bge-m3 behind find_similar()."""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from functools import lru_cache

from ..config import DATA_DIR
from ..normalize import to_traditional

MIN_SIMILARITY = 0.10
TOP_K = 3
_WORD = re.compile(r"[a-z0-9]+|[一-鿿]+")


def _grams(text: str) -> Counter:
    grams: Counter = Counter()
    for token in _WORD.findall(text.lower()):
        if token[0] >= "一":
            grams.update(token[i:i + 2] for i in range(len(token) - 1))
        elif len(token) > 2:
            grams[token] += 1
    return grams


@lru_cache(maxsize=1)
def _index() -> tuple[list[dict], list[dict], dict]:
    cases = json.loads((DATA_DIR / "scam_cases.json").read_text(encoding="utf-8"))
    grams = [_grams(to_traditional(f"{c['description_en']} {c['description_zh']}")) for c in cases]
    df = Counter(g for doc in grams for g in doc)
    idf = {g: math.log((1 + len(cases)) / (1 + n)) + 1 for g, n in df.items()}
    return cases, [_vector(doc, idf) for doc in grams], idf


def _vector(grams: Counter, idf: dict) -> dict:
    vec = {g: (1 + math.log(n)) * idf[g] for g, n in grams.items() if g in idf}
    norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
    return {g: v / norm for g, v in vec.items()}


def find_similar(text: str, top_k: int = TOP_K) -> list[dict]:
    cases, vectors, idf = _index()
    query = _vector(_grams(text), idf)
    scored = [(sum(w * vec.get(g, 0.0) for g, w in query.items()), case) for case, vec in zip(cases, vectors)]
    scored.sort(key=lambda item: item[0], reverse=True)
    return [
        {"title": c["title"], "title_zh": c["title_zh"], "similarity": round(s, 2), "source": c["source"]}
        for s, c in scored[:top_k] if s >= MIN_SIMILARITY
    ]
