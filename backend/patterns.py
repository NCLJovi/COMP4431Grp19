"""Translate rule hits into the plain pattern names the Streamlit frontend understands.

frontend/response_templates.py (PATTERN_PLAIN) holds one plain-English sentence per name, so a new
name added here needs a matching line there.
"""
from __future__ import annotations

import re

from . import wording
from .normalize import to_traditional
from .schemas import TriggeredRule

MAX_PATTERNS = 6

# rule id -> pattern name. Mitigating rules (M*) and compound rules (C*) are left out on purpose:
# compound rules only combine base facts that already appear here.
RULE_TO_PATTERN: dict[str, str] = {
    "R1": "urgency",
    "R2": "account problem",
    "R3": "password request",
    "R4": "personal details",          # NEW
    "R5": "money request",
    "R6": "government impersonation",
    "R7": "bank impersonation",        # becomes "parcel" for courier brands, see below
    "R8": "parcel",
    "R9": "prize",
    "R10": "investment",
    "R11": "job offer",
    "R12": "secrecy",                  # NEW
    "R13": "family impersonation",     # NEW
    "R14": "private chat",             # NEW
    "R15": "link",
    "R16": "link",
    "R17": "tech support",
    "R18": "money request",            # becomes "crypto" when the match names a coin
    "R19": "refund",                   # NEW
    "R20": "automated call",           # NEW
    "R21": "government impersonation",
    "R22": "account problem",
    "R23": "unexpected charge",        # NEW
    "R24": "gambling",                 # NEW
    "R25": "phone number",             # NEW
    "R26": "money request",
    "R27": "romance",
    "U1": "link",
}

# Used when the score is medium/high but no single rule explains it (e.g. similarity alone).
FALLBACK_PATTERN = "known scam pattern"  # NEW

NEW_PATTERN_NAMES = ("personal details", "secrecy", "family impersonation", "private chat",
                     "refund", "automated call", "unexpected charge", "gambling", "phone number", FALLBACK_PATTERN)

_COURIER = re.compile(to_traditional(r"sf express|hong ?kong post|dhl|fedex|順豐|郵政"), re.IGNORECASE)
_CRYPTO = re.compile(to_traditional(r"usdt|bitcoin|btc|crypto|ethereum|比特|泰達|虛擬貨幣"), re.IGNORECASE)


def _name_for(rule: TriggeredRule, text: str) -> str | None:
    name = RULE_TO_PATTERN.get(rule.id)
    if name is None:
        return None
    matched = text[rule.span[0]:rule.span[1]] if rule.span else ""
    if rule.id == "R7" and _COURIER.search(matched):
        return "parcel"
    if rule.id == "R18" and _CRYPTO.search(matched):
        return "crypto"
    return name


def matched_patterns(rules: list[TriggeredRule], text: str, risk_level: str) -> list[str]:
    """Strongest signs first, no duplicates, at most MAX_PATTERNS."""
    names: list[str] = []
    for rule in sorted(rules, key=lambda r: -r.weight):
        if rule.weight <= 0:
            continue
        # A brand name or "Hi Mum" alone proves nothing, so do not list it as a reason on a green verdict.
        if rule.id in ("R7", "R13") and risk_level == "low":
            continue
        name = _name_for(rule, text)
        if name and name not in names:
            names.append(name)
    if not names and risk_level != "low":
        names.append(FALLBACK_PATTERN)
    return names[:MAX_PATTERNS]


def short_explanation(risk_level: str, patterns: list[str]) -> str:
    """One plain sentence of at most 20 words, as docs/API_CONTRACT.md requires."""
    count = len(patterns)
    if risk_level in ("high", "medium"):
        signs = wording.ONE_SIGN if count == 1 else wording.MANY_SIGNS.format(count=count)
        return wording.SHORT_EXPLANATION[risk_level].format(signs=signs)
    return wording.SHORT_EXPLANATION["low_with_sign" if count else "low_clear"]
