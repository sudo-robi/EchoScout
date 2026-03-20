from fastapi.testclient import TestClient
import io
import math
import struct
import wave

from app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True


def test_research_endpoint_with_unconfigured_keys_still_responds():
    payload = {"query": "latest ai agent frameworks", "max_sources": 3, "max_hops": 1}
    response = client.post("/api/research", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["query"] == payload["query"]
    assert "summary" in body
    assert "synthesis_provider" in body
    assert "warnings" in body


def test_stt_endpoint_with_direct_transcript():
    response = client.post("/api/stt", data={"transcript": "hello world"})
    assert response.status_code == 200
    assert response.json()["transcript"] == "hello world"


def test_research_stream_endpoint_returns_sse():
    payload = {"query": "ai agents in healthcare", "max_sources": 2, "max_hops": 1}
    response = client.post("/api/research/stream", json=payload)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")
    assert "event: result" in response.text


def test_vad_endpoint_accepts_wav():
    sample_rate = 16000
    duration_sec = 0.5
    frequency = 220.0
    amplitude = 8000

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        frames = bytearray()
        total_samples = int(sample_rate * duration_sec)
        for index in range(total_samples):
            sample = int(amplitude * math.sin(2 * math.pi * frequency * (index / sample_rate)))
            frames.extend(struct.pack("<h", sample))
        wav.writeframes(bytes(frames))

    response = client.post(
        "/api/vad",
        files={"audio_file": ("test.wav", buffer.getvalue(), "audio/wav")},
        data={"threshold": "0.01"},
    )

    assert response.status_code == 200
    body = response.json()
    assert "speech_detected" in body
    assert "speech_ratio" in body
