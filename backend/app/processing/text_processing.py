import re
from collections import Counter

from app.processing.credibility import score_credibility


def clean_text(raw: str) -> str:
    text = re.sub(r"\s+", " ", raw or "").strip()
    return text


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 150) -> list[str]:
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = max(0, end - overlap)
    return chunks


def score_chunk(chunk: str, query: str) -> float:
    query_terms = [word.lower() for word in re.findall(r"\w+", query) if len(word) > 2]
    if not query_terms:
        return 0.0
    words = [word.lower() for word in re.findall(r"\w+", chunk)]
    counts = Counter(words)
    score = sum(counts[term] for term in query_terms)
    return float(score) / max(1, len(words))


def rank_sources(query: str, sources: list[dict], limit: int) -> list[dict]:
    ranked = []
    for source in sources:
        content = clean_text(source.get("content", ""))
        chunk_scores = [score_chunk(chunk, query) for chunk in chunk_text(content)]
        best = max(chunk_scores) if chunk_scores else 0.0

        url = source.get("url", "")
        credibility = score_credibility(url=url, text=content)
        score = best + credibility

        enriched = dict(source)
        enriched["score"] = round(score, 5)
        enriched["credibility_score"] = credibility
        ranked.append(enriched)

    ranked.sort(key=lambda item: item.get("score", 0.0), reverse=True)
    return ranked[:limit]
