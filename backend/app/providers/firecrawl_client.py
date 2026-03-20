from __future__ import annotations

import httpx


class FirecrawlClient:
    def __init__(self, api_key: str | None, base_url: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    async def search(self, query: str, limit: int = 5) -> list[dict]:
        if not self.configured:
            return []

        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"query": query, "limit": limit}

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(f"{self.base_url}/search", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        results = data.get("data") or data.get("results") or []
        normalized = []
        for item in results:
            normalized.append(
                {
                    "title": item.get("title", "Untitled"),
                    "url": item.get("url", ""),
                    "snippet": item.get("description") or item.get("snippet") or "",
                }
            )
        return normalized

    async def scrape(self, url: str) -> dict:
        if not self.configured:
            return {"url": url, "content": ""}

        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"url": url, "formats": ["markdown"]}

        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(f"{self.base_url}/scrape", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        body = data.get("data", {})
        content = body.get("markdown") or body.get("content") or ""
        return {
            "url": url,
            "title": body.get("metadata", {}).get("title", "Untitled"),
            "content": content,
        }
