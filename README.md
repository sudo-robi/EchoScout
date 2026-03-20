# Voice Research Advanced MVP (Speech → Research → Speech)

This repository implements your architecture as a minimal end-to-end MVP:

- Voice/text query input
- Agent-like research orchestration
- Firecrawl search + page scraping
- Source ranking + synthesis (ElevenAgents-first)
- Optional ElevenLabs text-to-speech output
- Adaptive multi-hop query expansion
- Contradiction checks and credibility scoring
- Optional Pinecone memory recall + writeback
- Streaming research and streaming TTS endpoints

## Project Structure

- `backend/` FastAPI service with orchestration pipeline
- `frontend/` static browser UI (`index.html`)

## Quick Start

1) Create a Python environment and install dependencies:

```bash
cd /home/robi/Desktop/elvenlabs/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) Configure environment variables in `.env` directly:

```bash
cd /home/robi/Desktop/elvenlabs
${EDITOR:-nano} .env
```

3) Start backend API:

```bash
cd /home/robi/Desktop/elvenlabs/backend
set -a
source /home/robi/Desktop/elvenlabs/.env
set +a
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4) Serve frontend:

```bash
cd /home/robi/Desktop/elvenlabs/frontend
python3 -m http.server 5173
```

Open: `http://localhost:5173`

## API Endpoints

- `GET /health` service + provider status
- `POST /api/research` run orchestrated research
- `POST /api/research/stream` stream research progress + final result (SSE)
- `POST /api/stt` speech-to-text (or direct transcript passthrough)
- `POST /api/vad` voice-activity detection on WAV payload
- `POST /api/tts` text-to-speech via ElevenLabs
- `POST /api/tts/stream` stream audio bytes (`audio/mpeg`)

## Required Integrations

For your requirement to use both Firecrawl and ElevenAgents:

- `FIRECRAWL_API_KEY` is required for web retrieval.
- `RESEARCH_SYNTH_PROVIDER=elevenagents` makes ElevenAgents the synthesis path.
- `ELEVENAGENTS_API_KEY` and `ELEVENAGENTS_AGENT_ID` enable live ElevenAgents synthesis.

If ElevenAgents is not fully configured or temporarily unavailable, the backend returns a deterministic extractive fallback and includes warnings.

## STT

- `POST /api/stt` uses OpenAI transcription API only.

## Memory (Optional)

Enable retrieval memory with Pinecone + OpenAI embeddings:

- `MEMORY_ENABLED=true`
- `PINECONE_API_KEY=...`
- `PINECONE_INDEX_HOST=...` (index host only, no protocol)
- `OPENAI_API_KEY=...` (for embeddings)

## Notes on MVP Behavior

- If `FIRECRAWL_API_KEY` is missing, research returns no external sources.
- If ElevenAgents is unavailable, synthesis falls back to extractive summary.
- If `ELEVENLABS_API_KEY` is missing, TTS returns empty audio.

## Tests

```bash
cd /home/robi/Desktop/elvenlabs/backend
pytest -q
```

## Notes on Advanced Features

- Multi-hop planning now expands queries adaptively from discovered keywords.
- Credibility scoring combines authority, recency, and citation signals.
- Contradiction checker flags potentially conflicting claims across sources.
- `STRICT_PROVIDER_MODE=true` enforces Firecrawl + configured synthesizer before processing.
