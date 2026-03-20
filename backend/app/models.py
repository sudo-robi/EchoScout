from pydantic import BaseModel, Field
from typing import Literal


class ResearchRequest(BaseModel):
    query: str = Field(..., min_length=3)
    max_sources: int = Field(default=5, ge=1, le=10)
    max_hops: int = Field(default=1, ge=1, le=3)


class SourceItem(BaseModel):
    title: str
    url: str
    snippet: str | None = None
    content: str | None = None
    score: float | None = None


class ResearchResponse(BaseModel):
    query: str
    summary: str
    key_points: list[str]
    citations: list[SourceItem]
    synthesis_provider: str
    warnings: list[str] = []
    contradictions: list[str] = []
    research_trace: list[str] = []


class STTResponse(BaseModel):
    transcript: str


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1)
    voice_id: str | None = None


class TTSResponse(BaseModel):
    audio_base64: str
    mime_type: str = "audio/mpeg"


class VADResponse(BaseModel):
    speech_detected: bool
    speech_ratio: float
    threshold: float


class PersonaResearchRequest(ResearchRequest):
    persona: Literal["analyst", "skeptic", "journalist", "policy_advisor"] = "analyst"
    continue_from_memory: bool = False
    challenge_source_url: str | None = None
    include_audio: bool = False
    voice_id: str | None = None


class PersonaResearchResponse(BaseModel):
    query: str
    persona: str
    spoken_script: str
    summary: str
    key_points: list[str]
    citations: list[SourceItem]
    continuity_notes: list[str] = []
    challenge_response: str | None = None
    audio_base64: str | None = None
    mime_type: str = "audio/mpeg"
    warnings: list[str] = []
    research_trace: list[str] = []


class SourceChallengeRequest(ResearchRequest):
    source_url: str = Field(..., min_length=5)


class SourceChallengeResponse(BaseModel):
    source_url: str
    challenge_prompt: str
    response: str
    citations: list[SourceItem]
    warnings: list[str] = []


class DebateRequest(ResearchRequest):
    proposition: str | None = None
    include_audio: bool = False
    pro_voice_id: str | None = None
    con_voice_id: str | None = None


class DebateTurn(BaseModel):
    speaker: str
    stance: Literal["pro", "con"]
    text: str
    citations: list[SourceItem]
    audio_base64: str | None = None


class DebateResponse(BaseModel):
    proposition: str
    turns: list[DebateTurn]
    arbitration: str
    contradictions: list[str] = []
    warnings: list[str] = []
    research_trace: list[str] = []
