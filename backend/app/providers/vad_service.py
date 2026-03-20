from __future__ import annotations

import io
import math
import struct
import wave


class VADService:
    def detect_speech(self, audio_bytes: bytes, threshold: float = 0.02) -> tuple[bool, float]:
        with wave.open(io.BytesIO(audio_bytes), "rb") as wav:
            sample_width = wav.getsampwidth()
            frame_rate = wav.getframerate()
            channels = wav.getnchannels()
            frames = wav.readframes(wav.getnframes())

        samples = self._to_mono_samples(frames=frames, sample_width=sample_width, channels=channels)
        if not samples:
            return False, 0.0

        chunk_ms = 30
        samples_per_chunk = int(frame_rate * (chunk_ms / 1000.0))
        if samples_per_chunk <= 0:
            return False, 0.0

        chunks = [samples[i : i + samples_per_chunk] for i in range(0, len(samples), samples_per_chunk) if samples[i : i + samples_per_chunk]]
        if not chunks:
            return False, 0.0

        max_rms = float((2 ** (8 * sample_width - 1)) - 1)
        speech_chunks = 0
        for chunk in chunks:
            rms = self._rms(chunk)
            energy = rms / max_rms
            if energy >= threshold:
                speech_chunks += 1

        ratio = speech_chunks / len(chunks)
        return ratio > 0.2, round(ratio, 4)

    def _to_mono_samples(self, frames: bytes, sample_width: int, channels: int) -> list[int]:
        if sample_width != 2:
            raise ValueError("Only 16-bit WAV is supported for VAD")

        count = len(frames) // sample_width
        unpacked = struct.unpack("<" + "h" * count, frames)
        if channels == 1:
            return list(unpacked)

        mono: list[int] = []
        for index in range(0, len(unpacked), channels):
            window = unpacked[index : index + channels]
            if not window:
                continue
            mono.append(int(sum(window) / len(window)))
        return mono

    def _rms(self, chunk: list[int]) -> float:
        if not chunk:
            return 0.0
        power = sum(sample * sample for sample in chunk) / len(chunk)
        return math.sqrt(power)
