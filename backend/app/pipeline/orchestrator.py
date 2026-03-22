from __future__ import annotations

from app.pipeline.graph_runtime import AgentGraphRuntime


class ResearchOrchestrator:
    def __init__(self, firecrawl_client, synthesis_client, memory_client=None, tavily_client=None):
        self.runtime = AgentGraphRuntime(
            firecrawl_client=firecrawl_client,
            synthesis_client=synthesis_client,
            memory_client=memory_client,
            tavily_client=tavily_client,
        )

    async def run(self, query: str, max_sources: int = 5, max_hops: int = 1) -> dict:
        return await self.runtime.execute(query=query, max_sources=max_sources, max_hops=max_hops)
