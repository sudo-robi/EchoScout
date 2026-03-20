from __future__ import annotations

import base64
import httpx


class ElevenLabsClient:
    def __init__(self, api_key: str | None, base_url: str, default_voice_id: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.default_voice_id = default_voice_id

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    async def tts(self, text: str, voice_id: str | None = None) -> dict:
        selected_voice = voice_id or self.default_voice_id
        if not self.configured:
            return {
                "audio_base64": "",
                "mime_type": "audio/mpeg",
                "warning": "ELEVENLABS_API_KEY is not configured",
            }

        audio_bytes = await self.tts_bytes(text=text, voice_id=selected_voice)

        return {
            "audio_base64": base64.b64encode(audio_bytes).decode("utf-8"),
            "mime_type": "audio/mpeg",
        }

    async def tts_bytes(self, text: str, voice_id: str | None = None) -> bytes:
        selected_voice = voice_id or self.default_voice_id
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
        }

        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(
                f"{self.base_url}/text-to-speech/{selected_voice}",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            return response.content
