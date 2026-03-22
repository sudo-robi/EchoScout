from __future__ import annotations

from tavily import AsyncTavilyClient


class TavilyClient:
    def __init__(self, api_key: str | None, search_depth: str = "basic"):
        self.api_key = api_key
        self.search_depth = search_depth
        if api_key:
            self._client = AsyncTavilyClient(api_key=api_key)
        else:
            self._client = None

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    async def search(self, query: str, limit: int = 5) -> list[dict]:
        if not self.configured or self._client is None:
            return []

        response = await self._client.search(
            query=query,
            max_results=limit,
            search_depth=self.search_depth,
        )

        normalized = []
        for item in response.get("results", []):
            normalized.append(
                {
                    "title": item.get("title", "Untitled"),
                    "url": item.get("url", ""),
                    "snippet": item.get("content", ""),
                }
            )
        return normalized

    async def extract(self, urls: list[str]) -> list[dict]:  # noqa: Future hook for Firecrawl scrape fallback
        if not self.configured or self._client is None:
            return []

        response = await self._client.extract(urls=urls[:20])

        results = []
        for item in response.get("results", []):
            results.append(
                {
                    "url": item.get("url", ""),
                    "title": "Extracted",
                    "content": item.get("raw_content", "") or item.get("text", ""),
                }
            )
        return results
