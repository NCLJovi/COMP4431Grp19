"""Ollama client. The LLM writes wording only: the risk score always comes from the rule engine, so a
message that tries to manipulate the model cannot lower its own score. Every failure falls back to a template."""
from __future__ import annotations

import json
import re

import httpx

from . import wording
from .config import LLM_ENABLED, OLLAMA_MODEL, OLLAMA_TIMEOUT_S, OLLAMA_URL

_THINK = re.compile(r"<think>.*?</think>", re.DOTALL)
_SAFE_CLAIM = re.compile(r"\b(?:is|looks|seems|appears) (?:safe|legitimate|genuine)\b|\bnot a scam\b|唔係騙案|不是騙案|不是骗局|係安全|是安全|沒有風險|冇風險", re.IGNORECASE)


async def _chat(system: str, user: str, temperature: float = 0.2, json_mode: bool = False) -> str | None:
    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "options": {"temperature": temperature},
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
    }
    if json_mode:
        payload["format"] = "json"
    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT_S) as client:
            response = await client.post(f"{OLLAMA_URL}/api/chat", json=payload)
            response.raise_for_status()
        content = response.json()["message"]["content"]
        return _THINK.sub("", content).strip() or None
    except (httpx.HTTPError, KeyError, ValueError, TypeError):
        return None


async def is_available() -> bool:
    if not LLM_ENABLED:
        return False
    try:
        async with httpx.AsyncClient(timeout=2) as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
            response.raise_for_status()
        return any(m.get("name") == OLLAMA_MODEL for m in response.json().get("models", []))
    except (httpx.HTTPError, ValueError, AttributeError):
        return False


async def explain(message: str, facts: dict, language: str) -> str | None:
    """Returns text, or None if the model is unavailable or contradicts the rule engine."""
    if not LLM_ENABLED:
        return None
    system = wording.LLM_EXPLAIN_PROMPT.format(language="Traditional Chinese, in Cantonese style" if language == "zh" else "English")
    user = f"{json.dumps(facts, ensure_ascii=False)}\n<message>\n{message.replace('</message>', '')}\n</message>"
    text = await _chat(system, user)
    if text and facts.get("risk_level") != "low" and _SAFE_CLAIM.search(text):
        return None
    return text


async def classify(message: str) -> bool | None:
    """LLM-only baseline for evaluation. True means scam, None means no usable answer."""
    text = await _chat(wording.LLM_CLASSIFY_PROMPT, f"<message>\n{message.replace('</message>', '')}\n</message>", 0.0, json_mode=True)
    if not text:
        return None
    try:
        label = json.loads(text).get("label")
    except (ValueError, AttributeError):
        return None
    return {"scam": True, "legit": False}.get(label)
