from __future__ import annotations

import re
from datetime import datetime
from urllib.parse import urlparse


HIGH_AUTHORITY = {
    "reuters.com": 0.16,
    "apnews.com": 0.16,
    "nature.com": 0.2,
    "science.org": 0.2,
    "who.int": 0.2,
    "gov": 0.2,
    "edu": 0.15,
    "org": 0.07,
}


def _domain_score(url: str) -> float:
    domain = urlparse(url).netloc.lower()
    if not domain:
        return 0.0

    for key, score in HIGH_AUTHORITY.items():
        if key in domain or domain.endswith(f".{key}"):
            return score
    return 0.03


def _recency_score(text: str) -> float:
    years = [int(y) for y in re.findall(r"\b(20\d{2})\b", text)]
    if not years:
        return 0.0

    current = datetime.utcnow().year
    freshest = max(years)
    gap = max(0, current - freshest)
    if gap <= 1:
        return 0.2
    if gap <= 3:
        return 0.1
    if gap <= 5:
        return 0.05
    return 0.0


def _citation_score(text: str) -> float:
    markers = [
        "according to",
        "source:",
        "study",
        "report",
        "published",
        "references",
        "cited",
    ]
    lower = text.lower()
    hits = sum(lower.count(marker) for marker in markers)
    return min(0.2, hits * 0.02)


def score_credibility(url: str, text: str) -> float:
    return round(_domain_score(url) + _recency_score(text) + _citation_score(text), 5)
