from __future__ import annotations

import asyncio
import re
from collections import Counter

from app.processing.contradiction import detect_contradictions
from app.processing.text_processing import clean_text, rank_sources


STOPWORDS = {
    "this",
    "that",
    "with",
    "from",
    "have",
    "will",
    "about",
    "latest",
    "updates",
    "research",
    "analysis",
    "report",
    "their",
    "there",
    "which",
}


class AgentGraphRuntime:
    def __init__(self, firecrawl_client, synthesis_client, memory_client=None):
        self.firecrawl_client = firecrawl_client
        self.synthesis_client = synthesis_client
        self.memory_client = memory_client

    async def execute(self, query: str, max_sources: int, max_hops: int) -> dict:
        trace: list[str] = ["planner:initialized"]
        warnings: list[str] = []
        planned_queries = [query.strip()]

        if not self.firecrawl_client.configured:
            warnings.append("FIRECRAWL_API_KEY is missing; web research cannot run")

        memory_context = []
        if self.memory_client is not None:
            memory_context = await self.memory_client.retrieve_similar(query, top_k=3)
            if memory_context:
                trace.append("memory:retrieved")

        candidates: list[dict] = []
        seen_urls: set[str] = set()

        for hop in range(max_hops):
            trace.append(f"planner:hop-{hop + 1}")
            hop_queries = planned_queries[-2:] if hop > 0 else planned_queries[:1]

            for planned in hop_queries:
                search_hits = await self.firecrawl_client.search(planned, limit=max_sources)
                trace.append(f"crawler:search:{planned}")
                if not search_hits:
                    continue

                scrape_tasks = [self.firecrawl_client.scrape(item["url"]) for item in search_hits if item.get("url")]
                scrape_results = await asyncio.gather(*scrape_tasks, return_exceptions=True)

                for hit, scraped in zip(search_hits, scrape_results):
                    url = hit.get("url", "")
                    if not url or url in seen_urls:
                        continue
                    seen_urls.add(url)

                    if isinstance(scraped, Exception):
                        content = hit.get("snippet", "")
                    else:
                        content = clean_text(scraped.get("content", ""))

                    candidates.append(
                        {
                            "title": hit.get("title", "Untitled"),
                            "url": url,
                            "snippet": hit.get("snippet", ""),
                            "content": content,
                        }
                    )

            if hop + 1 < max_hops:
                adaptive_queries = self._adaptive_queries(query=query, sources=candidates)
                if adaptive_queries:
                    planned_queries.extend(adaptive_queries)
                    trace.append("planner:adaptive-expansion")

        ranked = rank_sources(query=query, sources=candidates, limit=max_sources)
        contradictions = detect_contradictions(ranked)
        if contradictions:
            warnings.append("Potential source contradictions detected")
            trace.append("checker:contradictions")

        synthesis = await self.synthesis_client.summarize(query=query, sources=ranked)
        trace.append("synthesizer:complete")

        summary = synthesis.get("summary", "")
        if memory_context:
            memory_lines = [f"Past research: {item.get('summary', '')}" for item in memory_context[:2] if item.get("summary")]
            if memory_lines:
                summary = "\n".join(memory_lines + [summary])

        if self.memory_client is not None:
            await self.memory_client.upsert_research(query=query, summary=summary, sources=ranked)
            trace.append("memory:upserted")

        return {
            "summary": summary,
            "key_points": synthesis.get("key_points", []),
            "sources": ranked,
            "synthesis_provider": synthesis.get("provider", "unknown"),
            "warnings": warnings,
            "contradictions": contradictions,
            "research_trace": trace,
        }

    def _adaptive_queries(self, query: str, sources: list[dict]) -> list[str]:
        if not sources:
            return []

        text_blob = " ".join((s.get("content") or s.get("snippet") or "")[:1200] for s in sources[:6])
        words = [w.lower() for w in re.findall(r"\b[a-zA-Z]{4,}\b", text_blob)]
        words = [w for w in words if w not in STOPWORDS]

        if not words:
            return []

        common = [w for w, _ in Counter(words).most_common(4)]
        expansions = [f"{query} {term} latest" for term in common[:2]]
        return expansions
