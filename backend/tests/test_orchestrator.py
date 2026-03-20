import asyncio

from app.pipeline.orchestrator import ResearchOrchestrator


class FakeFirecrawl:
    configured = True

    async def search(self, query: str, limit: int = 5):
        return [
            {"title": "A", "url": "https://example.org/a", "snippet": "quantum chip update"},
            {"title": "B", "url": "https://example.com/b", "snippet": "funding round"},
        ][:limit]

    async def scrape(self, url: str):
        return {"url": url, "content": "quantum startup announced new funding and hardware milestone"}


class FakeSynthesis:
    async def summarize(self, query: str, sources: list[dict]):
        return {
            "summary": f"Summary for: {query}",
            "key_points": ["point1", "point2"],
            "provider": "elevenagents",
        }


def test_orchestrator_pipeline_returns_ranked_sources():
    orchestrator = ResearchOrchestrator(firecrawl_client=FakeFirecrawl(), synthesis_client=FakeSynthesis())

    result = asyncio.run(orchestrator.run(query="quantum startups", max_sources=2, max_hops=1))

    assert "summary" in result
    assert result["summary"].startswith("Summary for")
    assert len(result["sources"]) == 2
    assert result["sources"][0]["score"] >= result["sources"][1]["score"]
    assert result["synthesis_provider"] == "elevenagents"
