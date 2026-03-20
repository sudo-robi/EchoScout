from __future__ import annotations

import httpx


class LLMClient:
    def __init__(self, api_key: str | None, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    async def summarize(self, query: str, sources: list[dict]) -> dict:
        if not sources:
            return {
                "summary": "No reliable sources were retrieved. Configure Firecrawl and retry.",
                "key_points": ["No sources available"],
            }

        if not self.configured:
            bullets = []
            for item in sources[:5]:
                title = item.get("title", "Untitled")
                snippet = (item.get("content") or item.get("snippet") or "")[:180]
                bullets.append(f"{title}: {snippet}")
            return {
                "summary": "\n".join(bullets),
                "key_points": [f"Reviewed {len(sources)} sources", "LLM API key not configured"],
            }

        condensed_sources = []
        for source in sources[:8]:
            condensed_sources.append(
                {
                    "title": source.get("title"),
                    "url": source.get("url"),
                    "content": (source.get("content") or source.get("snippet") or "")[:2400],
                }
            )

        system_prompt = (
            "You are a research analyst. Use only provided sources. Return JSON with keys: "
            "summary (string), key_points (array of strings). Include no markdown."
        )

        user_prompt = {
            "query": query,
            "instructions": [
                "Extract key developments",
                "Remove duplicate points",
                "Stay source-grounded",
                "Keep concise and factual",
            ],
            "sources": condensed_sources,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": str(user_prompt)},
            ],
        }

        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        content = data["choices"][0]["message"]["content"]
        try:
            import json

            parsed = json.loads(content)
            return {
                "summary": parsed.get("summary", "No summary"),
                "key_points": parsed.get("key_points", []),
            }
        except Exception:
            return {
                "summary": content,
                "key_points": [],
            }
