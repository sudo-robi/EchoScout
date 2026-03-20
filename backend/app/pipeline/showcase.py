from __future__ import annotations

import re
from urllib.parse import urlparse


PERSONA_INTROS = {
    "analyst": "As your analyst, here is the evidence-backed brief.",
    "skeptic": "As your skeptic, here is what might be overstated.",
    "journalist": "As your journalist, here is the balanced story so far.",
    "policy_advisor": "As your policy advisor, here are implications and risks to watch.",
}


class ResearchShowcase:
    def __init__(self, orchestrator, memory_client, tts_client):
        self.orchestrator = orchestrator
        self.memory_client = memory_client
        self.tts_client = tts_client

    async def persona_mode(
        self,
        query: str,
        max_sources: int,
        max_hops: int,
        persona: str,
        continue_from_memory: bool,
        challenge_source_url: str | None,
        include_audio: bool,
        voice_id: str | None,
    ) -> dict:
        result = await self.orchestrator.run(query=query, max_sources=max_sources, max_hops=max_hops)

        continuity_notes: list[str] = []
        if continue_from_memory and self.memory_client is not None:
            memories = await self.memory_client.retrieve_similar(query, top_k=3)
            continuity_notes = self._build_continuity_notes(memories)

        spoken_script = self._build_persona_script(
            query=query,
            persona=persona,
            key_points=result.get("key_points", []),
            sources=result.get("sources", []),
            continuity_notes=continuity_notes,
        )

        challenge_response = None
        if challenge_source_url:
            challenge_response = self._build_source_challenge(challenge_source_url, result.get("sources", []), query)
            if challenge_response:
                spoken_script = f"{spoken_script}\n\nChallenge response: {challenge_response}"

        audio_base64 = None
        mime_type = "audio/mpeg"
        if include_audio:
            audio = await self.tts_client.tts(spoken_script, voice_id=voice_id)
            audio_base64 = audio.get("audio_base64")
            mime_type = audio.get("mime_type", "audio/mpeg")

        return {
            "query": query,
            "persona": persona,
            "spoken_script": spoken_script,
            "summary": result.get("summary", ""),
            "key_points": result.get("key_points", []),
            "citations": result.get("sources", []),
            "continuity_notes": continuity_notes,
            "challenge_response": challenge_response,
            "audio_base64": audio_base64,
            "mime_type": mime_type,
            "warnings": result.get("warnings", []),
            "research_trace": result.get("research_trace", []),
        }

    async def challenge_source(self, query: str, max_sources: int, max_hops: int, source_url: str) -> dict:
        result = await self.orchestrator.run(query=query, max_sources=max_sources, max_hops=max_hops)
        response = self._build_source_challenge(source_url, result.get("sources", []), query)

        return {
            "source_url": source_url,
            "challenge_prompt": "challenge that source",
            "response": response,
            "citations": result.get("sources", []),
            "warnings": result.get("warnings", []),
        }

    async def debate_mode(
        self,
        query: str,
        proposition: str | None,
        max_sources: int,
        max_hops: int,
        include_audio: bool,
        pro_voice_id: str | None,
        con_voice_id: str | None,
    ) -> dict:
        result = await self.orchestrator.run(query=query, max_sources=max_sources, max_hops=max_hops)
        sources = result.get("sources", [])
        proposition_text = proposition or f"Should we trust the current evidence on: {query}?"

        pro_sources = sources[:2]
        con_sources = sources[2:4] if len(sources) > 2 else sources[:2]

        pro_text = self._build_argument("pro", proposition_text, pro_sources)
        con_text = self._build_argument("con", proposition_text, con_sources)

        turns = [
            {
                "speaker": "Voice A",
                "stance": "pro",
                "text": pro_text,
                "citations": pro_sources,
                "audio_base64": None,
            },
            {
                "speaker": "Voice B",
                "stance": "con",
                "text": con_text,
                "citations": con_sources,
                "audio_base64": None,
            },
        ]

        if include_audio:
            pro_audio = await self.tts_client.tts(pro_text, voice_id=pro_voice_id)
            con_audio = await self.tts_client.tts(con_text, voice_id=con_voice_id)
            turns[0]["audio_base64"] = pro_audio.get("audio_base64")
            turns[1]["audio_base64"] = con_audio.get("audio_base64")

        contradictions = result.get("contradictions", [])
        arbitration = self._arbitrate(contradictions, pro_sources, con_sources)

        return {
            "proposition": proposition_text,
            "turns": turns,
            "arbitration": arbitration,
            "contradictions": contradictions,
            "warnings": result.get("warnings", []),
            "research_trace": result.get("research_trace", []),
        }

    def _build_persona_script(
        self,
        query: str,
        persona: str,
        key_points: list[str],
        sources: list[dict],
        continuity_notes: list[str],
    ) -> str:
        intro = PERSONA_INTROS.get(persona, PERSONA_INTROS["analyst"])
        lines = [intro, f"Topic: {query}."]

        if continuity_notes:
            lines.append("Continuity from earlier work:")
            lines.extend([f"- {item}" for item in continuity_notes[:2]])

        if key_points:
            lines.append("Key findings:")
            for index, point in enumerate(key_points[:3]):
                citation = self._source_citation(sources[index] if index < len(sources) else None)
                lines.append(f"- {point} {citation}".strip())
        else:
            lines.append("No key findings were available yet.")

        return "\n".join(lines)

    def _build_argument(self, stance: str, proposition: str, sources: list[dict]) -> str:
        stance_prefix = "I support this proposition" if stance == "pro" else "I challenge this proposition"
        lines = [f"{stance_prefix}: {proposition}"]

        if not sources:
            lines.append("No source evidence is available yet.")
            return " ".join(lines)

        for source in sources[:2]:
            snippet = (source.get("snippet") or source.get("content") or "")[:170]
            citation = self._source_citation(source)
            lines.append(f"Evidence: {snippet} {citation}".strip())

        return " ".join(lines)

    def _source_citation(self, source: dict | None) -> str:
        if not source:
            return ""

        title = source.get("title") or "Unknown source"
        url = source.get("url") or ""
        domain = urlparse(url).netloc.replace("www.", "") if url else "unknown domain"
        text = (source.get("snippet") or source.get("content") or "")[:300]

        year_match = re.search(r"\b(20\d{2})\b", text)
        year = year_match.group(1) if year_match else "recent"
        return f"(According to {title} from {domain}, published {year}.)"

    def _build_source_challenge(self, source_url: str, sources: list[dict], query: str) -> str:
        matched = next((item for item in sources if item.get("url") == source_url), None)
        if not matched:
            return f"I could not find that source in current results for '{query}'."

        credibility = matched.get("credibility_score", 0)
        snippet = (matched.get("snippet") or matched.get("content") or "")[:200]
        citation = self._source_citation(matched)

        skepticism = "high" if credibility < 0.25 else "moderate" if credibility < 0.5 else "lower"
        return (
            f"Challenge accepted. This source has {skepticism} reliability confidence based on domain and evidence cues. "
            f"Claim under challenge: {snippet}. {citation}"
        )

    def _build_continuity_notes(self, memories: list[dict]) -> list[str]:
        notes = []
        for memory in memories[:3]:
            query = memory.get("query")
            summary = (memory.get("summary") or "")[:180]
            if query and summary:
                notes.append(f"Previously on '{query}': {summary}")
        return notes

    def _arbitrate(self, contradictions: list[str], pro_sources: list[dict], con_sources: list[dict]) -> str:
        if contradictions:
            return (
                "Arbitration: claims conflict across sources. Prioritize latest and highest-credibility citations before action."
            )

        if not pro_sources and not con_sources:
            return "Arbitration: insufficient evidence for either side."

        return "Arbitration: current evidence slightly favors the pro case, but monitor for emerging contradictory data."
