from __future__ import annotations

import httpx


class STTService:
    def __init__(self, openai_api_key: str | None, openai_base_url: str, openai_stt_model: str):
        self.openai_api_key = openai_api_key
        self.openai_base_url = openai_base_url.rstrip("/")
        self.openai_stt_model = openai_stt_model

    async def transcribe(self, audio_bytes: bytes, filename: str, content_type: str) -> str:
        return await self._transcribe_openai(audio_bytes=audio_bytes, filename=filename, content_type=content_type)

    async def _transcribe_openai(self, audio_bytes: bytes, filename: str, content_type: str) -> str:
        if not self.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY required for STT provider=openai")

        files = {
            "file": (filename or "audio.wav", audio_bytes, content_type or "audio/wav"),
        }
        data = {"model": self.openai_stt_model}
        headers = {"Authorization": f"Bearer {self.openai_api_key}"}

        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(
                f"{self.openai_base_url}/audio/transcriptions",
                headers=headers,
                data=data,
                files=files,
            )

        if response.status_code >= 400:
            raise RuntimeError(f"STT provider error: {response.text}")

        body = response.json()
        return body.get("text", "").strip()
