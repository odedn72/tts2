# 00 - Architecture Overview

**Date:** 2026-02-28
**Status:** Draft

## Goal

Define the high-level architecture for the TTS Web Application described in the
MRD (`docs/mrd/mrd.md`). This document establishes the component boundaries,
data flow, and integration patterns that all subsequent specs refer to.

**MRD traceability:** This overview addresses the structural needs of all P0
requirements (FR-001 through FR-011) and non-functional requirements NFR-001
through NFR-008.

## System Context

```
+---------------------------+          +-----------------------------+
|     Browser (React SPA)   |  HTTP    |     Python Backend          |
|                           | <------> |     (FastAPI, localhost)     |
|  - Two-panel dark UI      |          |  - REST API                 |
|  - Audio playback          |          |  - TTS provider abstraction |
|  - Text highlighting       |          |  - Chunking & stitching     |
+---------------------------+          +-----------------------------+
                                                |   |   |   |
                                       HTTPS    |   |   |   |
                                       calls    v   v   v   v
                                       +------+------+------+------+
                                       |Google| AWS  |Eleven| Open |
                                       |Cloud | Polly| Labs | AI   |
                                       | TTS  |      |      | TTS  |
                                       +------+------+------+------+
```

## Component Diagram

```
Frontend (React + TypeScript)
  |
  +-- AppShell                    # Root layout: two-panel dark theme
  |     +-- LeftPanel (Controls)
  |     |     +-- ProviderSelector      (FR-001)
  |     |     +-- VoiceSelector         (FR-002)
  |     |     +-- SpeedControl          (FR-009)
  |     |     +-- GenerateButton        (FR-004)
  |     |     +-- SettingsPanel         (FR-010)
  |     |
  |     +-- RightPanel (Text & Playback)
  |           +-- TextInputArea         (FR-003)
  |           +-- HighlightedTextView   (FR-006, FR-007)
  |           +-- AudioPlayer           (FR-005, FR-008)
  |           +-- ProgressIndicator     (FR-011)
  |
  +-- State Management (React Context + useReducer)
  |     +-- AppState (provider, voice, speed, text, audio, timing, status)
  |
  +-- API Client (typed fetch wrapper)

Backend (Python / FastAPI)
  |
  +-- API Layer (FastAPI routers)
  |     +-- POST /api/voices             # List voices for a provider
  |     +-- POST /api/generate           # Start TTS generation
  |     +-- GET  /api/generate/{job_id}/status  # Poll generation progress
  |     +-- GET  /api/audio/{job_id}     # Download generated audio
  |     +-- GET  /api/providers          # List providers and capabilities
  |     +-- GET  /api/settings           # Get current settings (no keys)
  |     +-- PUT  /api/settings           # Update settings
  |
  +-- TTS Provider Abstraction
  |     +-- TTSProvider (abstract base class)
  |     +-- GoogleCloudTTSProvider
  |     +-- AmazonPollyProvider
  |     +-- ElevenLabsProvider
  |     +-- OpenAITTSProvider
  |     +-- ProviderRegistry
  |
  +-- Text Processing
  |     +-- TextChunker              (FR-011)
  |     +-- TimingNormalizer          (FR-006, FR-007)
  |
  +-- Audio Processing
  |     +-- AudioStitcher            (FR-011)
  |     +-- AudioStore (temp file management)
  |
  +-- Job Manager
  |     +-- JobStore (in-memory dict)
  |     +-- GenerationJob lifecycle
  |
  +-- Configuration
        +-- Settings (env vars + optional .env file)
        +-- ProviderConfig per provider
```

## Data Flow: Generate Audio

```
User clicks Generate
        |
        v
Frontend ---POST /api/generate---> Backend
        { provider, voice_id, text, speed }
        |
        v
Backend creates GenerationJob (status=PENDING, job_id=uuid)
        |
        v
Returns { job_id } immediately (202 Accepted)
        |
        v
Backend (background task):
  1. TextChunker splits text into chunks
  2. For each chunk:
     a. Call TTSProvider.synthesize(chunk, voice, speed)
     b. Receive audio bytes + timing data
     c. Update job progress (chunk N of M)
  3. AudioStitcher combines chunks into single MP3
  4. TimingNormalizer merges per-chunk timing into document-level timing
  5. Job status = COMPLETED, store audio + timing
        |
        v
Frontend polls GET /api/generate/{job_id}/status
  Returns { status, progress, total_chunks, completed_chunks }
        |
        v
When COMPLETED:
  Frontend fetches GET /api/audio/{job_id}
  Response includes audio bytes + timing metadata
        |
        v
Frontend loads audio into HTML5 Audio element
  TimingData drives word/sentence highlighting during playback
```

## Key Architectural Decisions

### AD-1: Async background generation with polling
**Rationale:** Chapter-length text may take 30+ seconds to generate (NFR-001,
NFR-002). A synchronous HTTP request would time out or block the UI. Instead,
the backend accepts a generate request, returns a job ID immediately, and
processes chunks asynchronously. The frontend polls for progress.

**Alternatives considered:** WebSockets for real-time updates. Rejected because
polling is simpler for a single-user local app and avoids WebSocket complexity.
Server-Sent Events (SSE) is another option but polling is sufficient given the
simplicity requirements.

### AD-2: Provider abstraction via abstract base class
**Rationale:** The MRD explicitly requires each provider behind an abstract
interface (Technical Constraints). This enables adding new providers without
modifying existing code and allows each provider's unique timing data format
to be normalized into a common structure.

### AD-3: In-memory job store (no database)
**Rationale:** Single-user local application (MRD Section 8 -- no multi-user).
No persistence needed across restarts. A simple Python dict keyed by job_id
is sufficient. Audio files stored as temp files on disk.

### AD-4: Text chunking on the backend
**Rationale:** Each provider has different payload size limits. The backend
knows the provider-specific limits and can chunk accordingly. Chunks are
stitched server-side into a single audio file so the frontend always
receives a single MP3.

### AD-5: Timing data normalization
**Rationale:** Each provider returns timing/synchronization data in a different
format (MRD Risk table). The backend normalizes all timing data into a single
`TimingData` model (array of `{ word, start_ms, end_ms }`) so the frontend
highlighting logic is provider-agnostic.

### AD-6: Dark-themed two-panel React SPA
**Rationale:** Design spec mandates dark mode and two-panel layout. React is
required by MRD. TypeScript is chosen for type safety. No responsive design
needed (desktop only, NFR-008).

### AD-7: localhost-only binding
**Rationale:** NFR-005 requires the app only listens on localhost. FastAPI
will be configured to bind to `127.0.0.1` only.

## Cross-Cutting Concerns

| Concern | Approach |
|---------|----------|
| Error handling | Hierarchical error classes (see spec 11). Backend returns structured error responses. Frontend displays user-friendly messages. |
| Security | API keys stored server-side only (NFR-004). Never included in API responses. Settings endpoint returns key status (configured/not) but not key values. |
| Logging | Python `logging` module. Structured logs. No API keys in logs. |
| Testing | TDD per CLAUDE.md. All provider calls mocked. Frontend components tested with React Testing Library. |
| Configuration | Environment variables with `.env` file support via `python-dotenv`. |
