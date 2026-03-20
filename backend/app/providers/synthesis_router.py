from __future__ import annotations


class SynthesisRouter:
    def __init__(self, preferred_provider: str, elevenagents_client, llm_client):
        self.preferred_provider = (preferred_provider or "elevenagents").lower()
        self.elevenagents_client = elevenagents_client
        self.llm_client = llm_client

    async def summarize(self, query: str, sources: list[dict]) -> dict:
        if self.preferred_provider == "elevenagents":
            result = await self.elevenagents_client.summarize(query=query, sources=sources)
            return {
                "summary": result.get("summary", ""),
                "key_points": result.get("key_points", []),
                "provider": "elevenagents",
            }

        result = await self.llm_client.summarize(query=query, sources=sources)
        return {
            "summary": result.get("summary", ""),
            "key_points": result.get("key_points", []),
            "provider": "llm",
        }
