from dataclasses import dataclass
import os


@dataclass(slots=True)
class Settings:
    app_name: str = "Voice Research"
    app_env: str = os.getenv("APP_ENV", "dev")
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "8000"))

    firecrawl_api_key: str | None = os.getenv("FIRECRAWL_API_KEY")
    firecrawl_base_url: str = os.getenv("FIRECRAWL_BASE_URL", "https://api.firecrawl.dev/v1")

    tavily_api_key: str | None = os.getenv("TAVILY_API_KEY")
    search_provider: str = os.getenv("SEARCH_PROVIDER", "firecrawl")

    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    openai_stt_model: str = os.getenv("OPENAI_STT_MODEL", "gpt-4o-mini-transcribe")

    elevenlabs_api_key: str | None = os.getenv("ELEVENLABS_API_KEY")
    elevenlabs_base_url: str = os.getenv("ELEVENLABS_BASE_URL", "https://api.elevenlabs.io/v1")
    elevenlabs_voice_id: str = os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")

    research_synth_provider: str = os.getenv("RESEARCH_SYNTH_PROVIDER", "elevenagents")
    elevenagents_api_key: str | None = os.getenv("ELEVENAGENTS_API_KEY") or os.getenv("ELEVENLABS_API_KEY")
    elevenagents_base_url: str = os.getenv("ELEVENAGENTS_BASE_URL", "https://api.elevenlabs.io/v1")
    elevenagents_agent_id: str | None = os.getenv("ELEVENAGENTS_AGENT_ID")

    stt_provider: str = "openai"
    strict_provider_mode: bool = os.getenv("STRICT_PROVIDER_MODE", "false").lower() == "true"

    pinecone_api_key: str | None = os.getenv("PINECONE_API_KEY")
    pinecone_index_host: str | None = os.getenv("PINECONE_INDEX_HOST")
    pinecone_namespace: str = os.getenv("PINECONE_NAMESPACE", "voice-research")
    memory_enabled: bool = os.getenv("MEMORY_ENABLED", "false").lower() == "true"


settings = Settings()
