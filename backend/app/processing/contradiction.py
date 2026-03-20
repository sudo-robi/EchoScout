from __future__ import annotations

import re


NEGATION_TOKENS = {"not", "never", "no", "none", "without", "didn't", "can't"}


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]


def _topic_terms(sentence: str) -> set[str]:
    return {w.lower() for w in re.findall(r"\b[a-zA-Z]{4,}\b", sentence)}


def _has_negation(sentence: str) -> bool:
    words = {w.lower() for w in re.findall(r"\b[a-zA-Z']+\b", sentence)}
    return bool(words & NEGATION_TOKENS)


def detect_contradictions(sources: list[dict], limit: int = 8) -> list[str]:
    statements: list[tuple[str, str, bool]] = []

    for source in sources[:limit]:
        url = source.get("url", "")
        for sentence in _sentences(source.get("content", "")[:2000])[:8]:
            statements.append((url, sentence, _has_negation(sentence)))

    contradictions: list[str] = []
    for index, (url_a, sent_a, neg_a) in enumerate(statements):
        terms_a = _topic_terms(sent_a)
        if len(terms_a) < 3:
            continue

        for url_b, sent_b, neg_b in statements[index + 1 :]:
            if url_a == url_b:
                continue
            terms_b = _topic_terms(sent_b)
            overlap = len(terms_a & terms_b)
            if overlap < 3:
                continue

            if neg_a != neg_b:
                contradictions.append(
                    f"Potential contradiction between {url_a} and {url_b}: '{sent_a[:120]}' vs '{sent_b[:120]}'"
                )
                if len(contradictions) >= 5:
                    return contradictions

    return contradictions
