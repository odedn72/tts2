# 01 - Project Setup

**Date:** 2026-02-28
**Status:** Draft

## Goal

Define the tech stack, directory structure, and dependency list for the TTS Web
Application. This spec provides the developer with everything needed to
initialize the project.

**MRD traceability:** Technical Constraints (Section 7) -- React frontend,
Python backend, local-only deployment, macOS primary platform.

## Tech Stack

### Backend
| Technology | Version | Purpose |
|-----------|---------|---------|
| Python | 3.11+ | Runtime |
| FastAPI | 0.110+ | HTTP API framework |
| Uvicorn | 0.27+ | ASGI server |
| Pydantic | 2.x | Data validation and models |
| python-dotenv | 1.0+ | Environment variable loading |
| httpx | 0.27+ | Async HTTP client for TTS APIs |
| boto3 | 1.34+ | AWS Polly SDK |
| google-cloud-texttospeech | 2.16+ | Google Cloud TTS SDK |
| pydub | 0.25+ | Audio concatenation/stitching |
| pytest | 8.x | Testing framework |
| pytest-asyncio | 0.23+ | Async test support |
| pytest-cov | 5.x | Coverage reporting |
| respx | 0.21+ | Mock httpx requests in tests |
| moto | 5.x | Mock AWS services in tests |

### Frontend
| Technology | Version | Purpose |
|-----------|---------|---------|
| React | 18.x | UI framework |
| TypeScript | 5.x | Type-safe JavaScript |
| Vite | 5.x | Build tool and dev server |
| CSS Modules or vanilla CSS | -- | Styling (dark theme, no CSS framework needed) |
| Vitest | 1.x | Unit testing |
| React Testing Library | 15.x | Component testing |
| MSW (Mock Service Worker) | 2.x | API mocking in tests |

### Dev Tools
| Tool | Purpose |
|------|---------|
| Ruff | Python linting and formatting |
| ESLint | TypeScript/React linting |
| Prettier | Frontend code formatting |

## Directory Structure

```
ttl-take2/
  |
  +-- CLAUDE.md
  +-- docs/
  |     +-- mrd/
  |     |     +-- mrd.md
  |     +-- design/
  |     |     +-- design-spec.md
  |     +-- specs/
  |           +-- 00-architecture-overview.md
  |           +-- 01-project-setup.md
  |           +-- ...
  |
  +-- backend/
  |     +-- pyproject.toml           # Python project config, dependencies
  |     +-- .env.example             # Template for environment variables
  |     +-- src/
  |     |     +-- __init__.py
  |     |     +-- main.py            # FastAPI app creation, startup
  |     |     +-- config.py          # Settings, env var loading
  |     |     +-- api/
  |     |     |     +-- __init__.py
  |     |     |     +-- router.py        # Main API router
  |     |     |     +-- providers.py     # /api/providers endpoint
  |     |     |     +-- voices.py        # /api/voices endpoint
  |     |     |     +-- generate.py      # /api/generate endpoints
  |     |     |     +-- audio.py         # /api/audio endpoint
  |     |     |     +-- settings.py      # /api/settings endpoints
  |     |     |     +-- schemas.py       # Pydantic request/response models
  |     |     |
  |     |     +-- providers/
  |     |     |     +-- __init__.py
  |     |     |     +-- base.py          # TTSProvider ABC
  |     |     |     +-- registry.py      # ProviderRegistry
  |     |     |     +-- google_tts.py    # Google Cloud TTS implementation
  |     |     |     +-- amazon_polly.py  # Amazon Polly implementation
  |     |     |     +-- elevenlabs.py    # ElevenLabs implementation
  |     |     |     +-- openai_tts.py    # OpenAI TTS implementation
  |     |     |
  |     |     +-- processing/
  |     |     |     +-- __init__.py
  |     |     |     +-- chunker.py       # Text chunking logic
  |     |     |     +-- timing.py        # Timing data normalization
  |     |     |     +-- audio.py         # Audio stitching
  |     |     |
  |     |     +-- jobs/
  |     |     |     +-- __init__.py
  |     |     |     +-- manager.py       # Job lifecycle management
  |     |     |     +-- models.py        # Job data models
  |     |     |
  |     |     +-- errors.py             # Error hierarchy
  |     |
  |     +-- tests/
  |           +-- __init__.py
  |           +-- conftest.py           # Shared fixtures
  |           +-- test_config.py
  |           +-- api/
  |           |     +-- __init__.py
  |           |     +-- test_providers.py
  |           |     +-- test_voices.py
  |           |     +-- test_generate.py
  |           |     +-- test_audio.py
  |           |     +-- test_settings.py
  |           +-- providers/
  |           |     +-- __init__.py
  |           |     +-- test_base.py
  |           |     +-- test_registry.py
  |           |     +-- test_google_tts.py
  |           |     +-- test_amazon_polly.py
  |           |     +-- test_elevenlabs.py
  |           |     +-- test_openai_tts.py
  |           +-- processing/
  |           |     +-- __init__.py
  |           |     +-- test_chunker.py
  |           |     +-- test_timing.py
  |           |     +-- test_audio.py
  |           +-- jobs/
  |                 +-- __init__.py
  |                 +-- test_manager.py
  |
  +-- frontend/
        +-- package.json
        +-- tsconfig.json
        +-- vite.config.ts
        +-- index.html
        +-- src/
        |     +-- main.tsx               # Entry point
        |     +-- App.tsx                # Root component
        |     +-- App.css                # Global styles, dark theme
        |     +-- types/
        |     |     +-- index.ts         # Shared TypeScript types
        |     |     +-- api.ts           # API request/response types
        |     |     +-- provider.ts      # Provider-related types
        |     |     +-- audio.ts         # Audio/timing types
        |     |
        |     +-- api/
        |     |     +-- client.ts        # Typed API client
        |     |
        |     +-- state/
        |     |     +-- AppContext.tsx    # React Context + useReducer
        |     |     +-- reducer.ts       # State reducer
        |     |     +-- actions.ts       # Action types and creators
        |     |
        |     +-- components/
        |     |     +-- AppShell.tsx          # Two-panel layout
        |     |     +-- AppShell.css
        |     |     +-- LeftPanel/
        |     |     |     +-- LeftPanel.tsx
        |     |     |     +-- LeftPanel.css
        |     |     |     +-- ProviderSelector.tsx
        |     |     |     +-- VoiceSelector.tsx
        |     |     |     +-- SpeedControl.tsx
        |     |     |     +-- GenerateButton.tsx
        |     |     |     +-- SettingsPanel.tsx
        |     |     |
        |     |     +-- RightPanel/
        |     |           +-- RightPanel.tsx
        |     |           +-- RightPanel.css
        |     |           +-- TextInputArea.tsx
        |     |           +-- HighlightedTextView.tsx
        |     |           +-- HighlightedTextView.css
        |     |           +-- AudioPlayer.tsx
        |     |           +-- AudioPlayer.css
        |     |           +-- ProgressIndicator.tsx
        |     |
        |     +-- hooks/
        |           +-- useAudioPlayback.ts   # Audio element management
        |           +-- useHighlighting.ts    # Timing-driven highlighting
        |           +-- useGenerationPolling.ts # Poll job status
        |           +-- useProviders.ts       # Fetch providers/voices
        |
        +-- tests/
              +-- setup.ts               # Test setup (MSW, etc.)
              +-- api/
              |     +-- client.test.ts
              +-- components/
              |     +-- AppShell.test.tsx
              |     +-- ProviderSelector.test.tsx
              |     +-- VoiceSelector.test.tsx
              |     +-- SpeedControl.test.tsx
              |     +-- GenerateButton.test.tsx
              |     +-- TextInputArea.test.tsx
              |     +-- HighlightedTextView.test.tsx
              |     +-- AudioPlayer.test.tsx
              |     +-- ProgressIndicator.test.tsx
              +-- hooks/
              |     +-- useAudioPlayback.test.ts
              |     +-- useHighlighting.test.ts
              |     +-- useGenerationPolling.test.ts
              +-- state/
                    +-- reducer.test.ts

```

## Environment Variables

```bash
# .env.example

# Server
HOST=127.0.0.1
PORT=8000

# Google Cloud TTS
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Amazon Polly
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1

# ElevenLabs
ELEVENLABS_API_KEY=your_elevenlabs_key

# OpenAI TTS
OPENAI_API_KEY=your_openai_key

# Audio storage (temporary files)
AUDIO_STORAGE_DIR=/tmp/tts-app-audio
```

## Commands

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest                          # Run all backend tests
pytest --cov=src                # Run with coverage
uvicorn src.main:app --host 127.0.0.1 --port 8000  # Start backend

# Frontend
cd frontend
npm install
npm run dev                     # Start Vite dev server (proxied to backend)
npm test                        # Run Vitest
npm run build                   # Production build
```

## Vite Proxy Configuration

The Vite dev server should proxy `/api/*` requests to the backend at
`http://127.0.0.1:8000` so the frontend can call backend APIs without CORS
issues during development.

```typescript
// vite.config.ts (relevant snippet)
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: false,
      },
    },
  },
});
```

## Notes for Developer

1. Initialize the backend with `pyproject.toml` using the `[project]` table
   format. Include `[project.optional-dependencies]` with a `dev` group for
   test dependencies.
2. The frontend should be initialized with `npm create vite@latest frontend --
   template react-ts`.
3. All Python source code lives under `backend/src/` to keep it importable as
   a package.
4. Tests mirror the source structure under `backend/tests/` and
   `frontend/tests/`.
5. Remember: TDD -- write tests first, then implementation.
6. The backend serves the built frontend static files in production mode but
   during development the Vite dev server runs separately with a proxy.
