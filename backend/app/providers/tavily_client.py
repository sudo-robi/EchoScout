from __future__ import annotations

from tavily import AsyncTavilyClient


class TavilyClient:
    def __init__(self, api_key: str | None):
        self.api_key = api_key
        self._client: AsyncTavilyClient | None = (
            AsyncTavilyClient(api_key=api_key) if api_key else None
        )

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    async def search(self, query: str, limit: int = 5) -> list[dict]:
        if not self._client:
            return []

        response = await self._client.search(
            query=query,
            max_results=limit,
            search_depth="basic",
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

    async def scrape(self, url: str) -> dict:
        if not self._client:
            return {"url": url, "content": ""}

        response = await self._client.extract(urls=[url])

        results = response.get("results", [])
        if not results:
            return {"url": url, "title": "Untitled", "content": ""}

        first = results[0]
        return {
            "url": url,
            "title": first.get("title", "Untitled"),
            "content": first.get("raw_content", "") or first.get("text", ""),
        }
