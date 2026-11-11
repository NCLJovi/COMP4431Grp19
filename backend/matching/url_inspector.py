"""Basic URL Inspector. The URL is only read as text, apart from optional short-link expansion, which
sends a HEAD request to known shorteners, follows no redirect and never loads the destination page."""
from __future__ import annotations

import ipaddress
import json
import re
from functools import lru_cache
from urllib.parse import urlsplit

import httpx
import tldextract
from rapidfuzz.distance import Levenshtein

from ..config import DATA_DIR, URL_EXPAND_TIMEOUT_S

# suffix_list_urls=() keeps tldextract offline by using its bundled suffix list.
_extract = tldextract.TLDExtract(suffix_list_urls=(), cache_dir=None)

# Latin, Cyrillic and Greek hosts are allowed so homoglyphs are caught; CJK ends the URL.
_HOST = r"[a-z0-9Ͱ-ϿЀ-ӿ](?:[a-z0-9Ͱ-ϿЀ-ӿ-]*[a-z0-9Ͱ-ϿЀ-ӿ])?"
_PATH = r"(?:[/?#][a-z0-9\-._~%/?#&=+:@]*)?"
_URL = re.compile(rf"(?<![@a-zA-Z0-9.-])(?:(?:https?://)?(?:{_HOST}\.)+{_HOST}(?::\d+)?{_PATH})", re.IGNORECASE)

SUSPICIOUS_TLDS = {"wiki", "top", "xyz", "icu", "click", "cc", "vip", "shop", "buzz", "live", "rest", "cyou", "sbs", "site", "online", "info"}
SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd", "ow.ly", "cutt.ly", "rb.gy", "t.ly", "tiny.cc"}
_HOMOGLYPHS = str.maketrans({"0": "o", "1": "l", "3": "e", "5": "s", "7": "t", "$": "s", "@": "a"})
FLAG_VALUES = {"lookalike": 1.0, "homoglyph": 1.0, "punycode": 1.0, "ip_address": 1.0, "suspicious_tld": 0.6, "shortened": 0.6}


def flag_value(issue: str | None) -> float:
    return FLAG_VALUES.get(issue, 0.0)


@lru_cache(maxsize=1)
def _official() -> dict[str, str]:
    """Maps brand keyword to official domain, e.g. hsbc -> hsbc.com.hk."""
    return json.loads((DATA_DIR / "official_domains.json").read_text(encoding="utf-8"))


def _is_official(host: str) -> str | None:
    domains = set(_official().values()) | {"gov.hk"}
    return next((d for d in domains if host == d or host.endswith("." + d)), None)


def _check_lookalike(host: str, domain: str) -> tuple[str, str] | None:
    label = domain.lower()
    normalised = label.translate(_HOMOGLYPHS)
    words = re.split(r"[-.]", host)
    for brand, official in _official().items():
        compact = brand.replace("-", "")
        if label != compact and normalised == compact:
            return "homoglyph", official
        # Very short brands such as "sc" only count as a whole word, or "discount" would match.
        if brand in words or (len(compact) >= 4 and compact in label.replace("-", "")):
            return "lookalike", official
        # Short brands such as "dhl" would match too many unrelated words on edit distance.
        if len(compact) >= 5 and Levenshtein.distance(label, compact) <= 2:
            return "lookalike", official
    return None


def _expand(url: str) -> str | None:
    """Read the Location header of a known shortener. Failure just means no expansion."""
    try:
        response = httpx.head(url if "://" in url else f"https://{url}", follow_redirects=False, timeout=URL_EXPAND_TIMEOUT_S)
        return response.headers.get("location")
    except httpx.HTTPError:
        return None


def _inspect_one(raw: str, expand: bool) -> dict | None:
    url = raw.rstrip(".,;:!?")
    host = (urlsplit(url if "://" in url else f"//{url}").hostname or "").lower()
    if not host:
        return None
    try:
        ipaddress.ip_address(host)
        return {"url": url, "issue": "ip_address", "target": None}
    except ValueError:
        pass

    parts = _extract(host)
    if not parts.suffix or not parts.domain:
        return None
    registered = f"{parts.domain}.{parts.suffix}"
    official = _is_official(host)
    if official:
        return {"url": url, "issue": None, "target": official}
    if "xn--" in host:
        return {"url": url, "issue": "punycode", "target": None}
    if not host.isascii():
        target = next((d for b, d in _official().items() if b[0] in host), None)
        return {"url": url, "issue": "homoglyph", "target": target}
    if registered in SHORTENERS:
        finding = {"url": url, "issue": "shortened", "target": None}
        if expand:
            finding["expanded_url"] = _expand(url)
        return finding
    lookalike = _check_lookalike(host, parts.domain)
    if lookalike:
        return {"url": url, "issue": lookalike[0], "target": lookalike[1]}
    if parts.suffix.rsplit(".", 1)[-1] in SUSPICIOUS_TLDS:
        return {"url": url, "issue": "suspicious_tld", "target": None}
    return {"url": url, "issue": None, "target": None}


def inspect_urls(text: str, expand_short_urls: bool = False) -> list[dict]:
    findings = []
    for match in _URL.finditer(text):
        finding = _inspect_one(match.group(0), expand_short_urls)
        if finding:
            finding["span"] = [match.start(), match.start() + len(finding["url"])]
            findings.append(finding)
    return findings
