# TTS Reader

## Overview
A personal text-to-speech web application that runs locally. Users paste text
(up to chapter-length), select a TTS provider and voice, generate spoken audio,
and play it back with real-time word-by-word text highlighting. Supports four
TTS providers: Google Cloud TTS, Amazon Polly, ElevenLabs, OpenAI TTS.

See `docs/mrd/mrd.md` for full product requirements.
See `docs/design/design-spec.md` for UI/UX specifications.
See `docs/specs/` for architecture decisions and component specifications.

## Tech Stack

### Backend
- **Runtime:** Python 3.11+
- **Framework:** FastAPI with Uvicorn (ASGI)
- **Data Validation:** Pydantic v2
- **HTTP Client:** httpx (async, for ElevenLabs and OpenAI APIs)
- **AWS SDK:** boto3 (for Amazon Polly)
- **Google SDK:** google-cloud-texttospeech
- **Audio Processing:** pydub (requires ffmpeg system dependency)
- **Config:** pydantic-settings + python-dotenv
- **Testing:** pytest, pytest-asyncio, pytest-cov, respx, moto

### Frontend
- **Framework:** React 18 with TypeScript 5
- **Build Tool:** Vite 5
- **Styling:** CSS Modules / vanilla CSS (dark theme, no CSS framework)
- **State Management:** React Context + useReducer
- **Testing:** Vitest, React Testing Library, MSW (Mock Service Worker)

### Dev Tools
- **Python Linting:** Ruff
- **JS Linting:** ESLint + Prettier

## Project Structure
```
ttl-take2/
  backend/
    pyproject.toml
    .env.example
    src/
      __init__.py
      main.py              # FastAPI app, startup, lifespan
      config.py            # Settings, env var loading
      errors.py            # Error hierarchy
      api/                 # FastAPI route handlers
        __init__.py
        router.py
        schemas.py         # Pydantic request/response models
        providers.py       # /api/providers endpoint
        voices.py          # /api/voices endpoint
        generate.py        # /api/generate endpoints
        audio.py           # /api/audio endpoints
        settings.py        # /api/settings endpoints
      providers/           # TTS provider abstraction
        __init__.py
        base.py            # TTSProvider ABC
        registry.py        # ProviderRegistry
        google_tts.py
        amazon_polly.py
        elevenlabs.py
        openai_tts.py
      processing/          # Text and audio processing
        __init__.py
        chunker.py
        timing.py
        audio.py
      jobs/                # Generation job management
        __init__.py
        manager.py
        models.py
    tests/                 # Mirrors src/ structure
      ...
  frontend/
    package.json
    tsconfig.json
    vite.config.ts
    src/
      main.tsx
      App.tsx
      App.css              # Global dark theme styles
      types/               # TypeScript type definitions
      api/                 # API client
        client.ts
      state/               # React Context + reducer
        AppContext.tsx
        reducer.ts
        actions.ts
      components/          # React components
        AppShell.tsx
        LeftPanel/
        RightPanel/
      hooks/               # Custom hooks
        useAudioPlayback.ts
        useHighlighting.ts
        useGenerationPolling.ts
        useProviders.ts
    tests/                 # Component and hook tests
      ...
  docs/
    mrd/mrd.md
    design/design-spec.md
    specs/                 # Architecture specs (00-14)
```

## Commands

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest                              # Run all backend tests
pytest --cov=src                    # Run with coverage
uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload  # Dev server

# Frontend
cd frontend
npm install
npm run dev                         # Vite dev server (port 5173, proxied to backend)
npm test                            # Run Vitest
npm run build                       # Production build

# System dependency
brew install ffmpeg                 # Required by pydub for audio processing
```

## Conventions
- **TDD: Tests are written BEFORE implementation code**
- Type hints / strong typing where applicable
- Async/non-blocking I/O for all external calls
- All external integrations behind abstract interfaces (TTSProvider ABC)
- Configuration via environment variables (.env file supported)
- All user input validated at boundaries (Pydantic on backend, TypeScript on frontend)
- Comprehensive error handling -- never expose internals or API keys
- Tests mock all external dependencies (respx, moto, MSW)
- API keys stored server-side only; never sent to frontend
- Server binds to 127.0.0.1 only (localhost)
- Error responses use structured format: { error_code, message, details }
