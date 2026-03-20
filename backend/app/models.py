from pydantic import BaseModel, Field


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
