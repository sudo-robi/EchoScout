from __future__ import annotations

import base64
import json

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.config import settings
from app.memory.pinecone_memory import PineconeMemory
from app.models import (
    DebateRequest,
    DebateResponse,
    PersonaResearchRequest,
    PersonaResearchResponse,
    ResearchRequest,
    ResearchResponse,
    SourceChallengeRequest,
    SourceChallengeResponse,
    STTResponse,
    TTSRequest,
    TTSResponse,
    VADResponse,
)
from app.pipeline.orchestrator import ResearchOrchestrator
from app.pipeline.showcase import ResearchShowcase
from app.providers.elevenagents_client import ElevenAgentsClient
from app.providers.elevenlabs_client import ElevenLabsClient
from app.providers.firecrawl_client import FirecrawlClient
from app.providers.llm_client import LLMClient
from app.providers.stt_service import STTService
from app.providers.synthesis_router import SynthesisRouter
from app.providers.vad_service import VADService

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

firecrawl_client = FirecrawlClient(api_key=settings.firecrawl_api_key, base_url=settings.firecrawl_base_url)
llm_client = LLMClient(api_key=settings.openai_api_key, base_url=settings.openai_base_url, model=settings.openai_model)
elevenagents_client = ElevenAgentsClient(
    api_key=settings.elevenagents_api_key,
    base_url=settings.elevenagents_base_url,
    agent_id=settings.elevenagents_agent_id,
)
synthesis_router = SynthesisRouter(
    preferred_provider=settings.research_synth_provider,
    elevenagents_client=elevenagents_client,
    llm_client=llm_client,
)
elevenlabs_client = ElevenLabsClient(
    api_key=settings.elevenlabs_api_key,
    base_url=settings.elevenlabs_base_url,
    default_voice_id=settings.elevenlabs_voice_id,
)
memory_client = PineconeMemory(
    enabled=settings.memory_enabled,
    api_key=settings.pinecone_api_key,
    index_host=settings.pinecone_index_host,
    namespace=settings.pinecone_namespace,
    openai_api_key=settings.openai_api_key,
    openai_base_url=settings.openai_base_url,
)
orchestrator = ResearchOrchestrator(
    firecrawl_client=firecrawl_client,
    synthesis_client=synthesis_router,
    memory_client=memory_client,
)
showcase = ResearchShowcase(
    orchestrator=orchestrator,
    memory_client=memory_client,
    tts_client=elevenlabs_client,
)
stt_service = STTService(
    openai_api_key=settings.openai_api_key,
    openai_base_url=settings.openai_base_url,
    openai_stt_model=settings.openai_stt_model,
)
vad_service = VADService()


@app.get("/health")
async def health() -> dict:
    return {
        "ok": True,
        "firecrawl_configured": firecrawl_client.configured,
        "elevenagents_configured": elevenagents_client.configured,
        "llm_configured": llm_client.configured,
        "tts_configured": elevenlabs_client.configured,
        "stt_provider": settings.stt_provider,
        "memory_enabled": memory_client.configured,
        "research_synth_provider": settings.research_synth_provider,
    }


@app.post("/api/research", response_model=ResearchResponse)
async def research(payload: ResearchRequest) -> ResearchResponse:
    if settings.strict_provider_mode:
        if not firecrawl_client.configured:
            raise HTTPException(status_code=400, detail="STRICT_PROVIDER_MODE requires FIRECRAWL_API_KEY")
        if settings.research_synth_provider == "elevenagents" and not elevenagents_client.configured:
            raise HTTPException(status_code=400, detail="STRICT_PROVIDER_MODE requires ELEVENAGENTS_API_KEY and ELEVENAGENTS_AGENT_ID")

    result = await orchestrator.run(
        query=payload.query,
        max_sources=payload.max_sources,
        max_hops=payload.max_hops,
    )
    return ResearchResponse(
        query=payload.query,
        summary=result["summary"],
        key_points=result["key_points"],
        citations=result["sources"],
        synthesis_provider=result["synthesis_provider"],
        warnings=result["warnings"],
        contradictions=result.get("contradictions", []),
        research_trace=result.get("research_trace", []),
    )


@app.post("/api/research/persona", response_model=PersonaResearchResponse)
async def research_persona(payload: PersonaResearchRequest) -> PersonaResearchResponse:
    result = await showcase.persona_mode(
        query=payload.query,
        max_sources=payload.max_sources,
        max_hops=payload.max_hops,
        persona=payload.persona,
        continue_from_memory=payload.continue_from_memory,
        challenge_source_url=payload.challenge_source_url,
        include_audio=payload.include_audio,
        voice_id=payload.voice_id,
    )
    return PersonaResearchResponse(**result)


@app.post("/api/research/challenge", response_model=SourceChallengeResponse)
async def research_challenge(payload: SourceChallengeRequest) -> SourceChallengeResponse:
    result = await showcase.challenge_source(
        query=payload.query,
        max_sources=payload.max_sources,
        max_hops=payload.max_hops,
        source_url=payload.source_url,
    )
    return SourceChallengeResponse(**result)


@app.post("/api/research/debate", response_model=DebateResponse)
async def research_debate(payload: DebateRequest) -> DebateResponse:
    result = await showcase.debate_mode(
        query=payload.query,
        proposition=payload.proposition,
        max_sources=payload.max_sources,
        max_hops=payload.max_hops,
        include_audio=payload.include_audio,
        pro_voice_id=payload.pro_voice_id,
        con_voice_id=payload.con_voice_id,
    )
    return DebateResponse(**result)


@app.post("/api/research/stream")
async def research_stream(payload: ResearchRequest) -> StreamingResponse:
    async def event_stream():
        yield f"event: stage\ndata: {json.dumps({'step': 'planner', 'message': 'Planning research steps'})}\n\n"
        result = await orchestrator.run(
            query=payload.query,
            max_sources=payload.max_sources,
            max_hops=payload.max_hops,
        )
        yield f"event: stage\ndata: {json.dumps({'step': 'synthesizer', 'message': 'Synthesis complete'})}\n\n"
        yield f"event: result\ndata: {json.dumps(result)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/api/stt", response_model=STTResponse)
async def speech_to_text(
    transcript: str | None = Form(default=None),
    audio_file: UploadFile | None = File(default=None),
) -> STTResponse:
    if transcript:
        return STTResponse(transcript=transcript.strip())

    if not audio_file:
        raise HTTPException(status_code=400, detail="Provide transcript text or audio_file")

    audio_bytes = await audio_file.read()
    try:
        text = await stt_service.transcribe(
            audio_bytes=audio_bytes,
            filename=audio_file.filename or "audio.wav",
            content_type=audio_file.content_type or "audio/wav",
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return STTResponse(transcript=text)


@app.post("/api/vad", response_model=VADResponse)
async def vad_check(
    audio_file: UploadFile = File(...),
    threshold: float = Form(default=0.02),
) -> VADResponse:
    audio_bytes = await audio_file.read()
    try:
        speech_detected, speech_ratio = vad_service.detect_speech(audio_bytes=audio_bytes, threshold=threshold)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"VAD parsing error: {exc}") from exc
    return VADResponse(speech_detected=speech_detected, speech_ratio=speech_ratio, threshold=threshold)


@app.post("/api/tts", response_model=TTSResponse)
async def text_to_speech(payload: TTSRequest) -> TTSResponse:
    result = await elevenlabs_client.tts(payload.text, voice_id=payload.voice_id)
    if not result.get("audio_base64"):
        empty = base64.b64encode(b"").decode("utf-8")
        return TTSResponse(audio_base64=empty, mime_type="audio/mpeg")
    return TTSResponse(audio_base64=result["audio_base64"], mime_type=result.get("mime_type", "audio/mpeg"))


@app.post("/api/tts/stream")
async def text_to_speech_stream(payload: TTSRequest) -> StreamingResponse:
    if not elevenlabs_client.configured:
        raise HTTPException(status_code=400, detail="ELEVENLABS_API_KEY is required")

    audio_bytes = await elevenlabs_client.tts_bytes(text=payload.text, voice_id=payload.voice_id)

    async def audio_stream():
        chunk_size = 8192
        for index in range(0, len(audio_bytes), chunk_size):
            yield audio_bytes[index : index + chunk_size]

    return StreamingResponse(audio_stream(), media_type="audio/mpeg")
