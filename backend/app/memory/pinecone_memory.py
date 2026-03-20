from __future__ import annotations

import hashlib
import time

import httpx


class PineconeMemory:
    def __init__(
        self,
        enabled: bool,
        api_key: str | None,
        index_host: str | None,
        namespace: str,
        openai_api_key: str | None,
        openai_base_url: str,
    ):
        self.enabled = enabled
        self.api_key = api_key
        self.index_host = (index_host or "").rstrip("/")
        self.namespace = namespace
        self.openai_api_key = openai_api_key
        self.openai_base_url = openai_base_url.rstrip("/")

    @property
    def configured(self) -> bool:
        return bool(self.enabled and self.api_key and self.index_host and self.openai_api_key)

    async def retrieve_similar(self, query: str, top_k: int = 3) -> list[dict]:
        if not self.configured:
            return []

        vector = await self._embed(query)
        headers = {
            "Api-Key": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "vector": vector,
            "topK": top_k,
            "namespace": self.namespace,
            "includeMetadata": True,
        }

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(f"https://{self.index_host}/query", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        matches = data.get("matches", [])
        return [m.get("metadata", {}) for m in matches]

    async def upsert_research(self, query: str, summary: str, sources: list[dict]) -> None:
        if not self.configured:
            return

        vector = await self._embed(f"{query}\n{summary}")
        metadata = {
            "query": query,
            "summary": summary[:2000],
            "sources": ", ".join([s.get("url", "") for s in sources[:6]]),
            "timestamp": int(time.time()),
        }

        vector_id = hashlib.sha256(f"{query}:{metadata['timestamp']}".encode("utf-8")).hexdigest()[:24]

        headers = {
            "Api-Key": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "namespace": self.namespace,
            "vectors": [
                {
                    "id": vector_id,
                    "values": vector,
                    "metadata": metadata,
                }
            ],
        }

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(f"https://{self.index_host}/vectors/upsert", headers=headers, json=payload)
            response.raise_for_status()

    async def _embed(self, text: str) -> list[float]:
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "text-embedding-3-small",
            "input": text[:8000],
        }

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(f"{self.openai_base_url}/embeddings", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        return data["data"][0]["embedding"]
