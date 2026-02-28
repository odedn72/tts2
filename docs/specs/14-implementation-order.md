# 14 - Implementation Order

**Date:** 2026-02-28
**Status:** Draft

## Goal

Define the recommended implementation sequence for the developer agent. Each
phase builds on the previous one, enabling incremental testing and integration.

## Phases

### Phase 1: Project Scaffolding
**Spec:** 01 (Project Setup)
**Tasks:**
1. Initialize the backend Python project with `pyproject.toml`
2. Initialize the frontend React+TypeScript project with Vite
3. Set up testing frameworks (pytest, vitest, MSW)
4. Create the directory structure
5. Create `.env.example`
6. Verify `pytest` and `npm test` both run (with zero tests)
7. Configure Vite proxy to backend

**Deliverables:** Empty but runnable project with test infrastructure.

---

### Phase 2: Shared Data Models and Error Hierarchy
**Specs:** 02 (Data Models), 11 (Error Handling)
**Tasks:**
1. Write tests for all Pydantic models (serialization, validation)
2. Implement Pydantic models in `backend/src/api/schemas.py`
3. Write tests for the error hierarchy (correct codes, HTTP statuses)
4. Implement the error hierarchy in `backend/src/errors.py`
5. Write TypeScript types in `frontend/src/types/`

**Deliverables:** Validated data models, error classes, TypeScript types.

---

### Phase 3: Configuration
**Spec:** 12 (Configuration and Security)
**Tasks:**
1. Write tests for Settings loading from env vars
2. Implement Settings class with pydantic-settings
3. Write tests for RuntimeConfig (get/set/is_configured)
4. Implement RuntimeConfig
5. Write test for ffmpeg availability check
6. Implement startup checks

**Deliverables:** Configuration system that loads from env vars.

---

### Phase 4: Text Processing
**Spec:** 04 (Text Processing)
**Tasks:**
1. Write tests for TextChunker (all edge cases listed in spec)
2. Implement TextChunker
3. Write tests for TimingNormalizer (merge, estimate)
4. Implement TimingNormalizer
5. Write tests for sentence splitting utility

**Deliverables:** Working text chunker and timing normalizer with full test coverage.

---

### Phase 5: Audio Processing
**Spec:** 07 (Audio Processing)
**Tasks:**
1. Write tests for AudioStitcher (single, multiple, error cases)
2. Implement AudioStitcher using pydub
3. Write tests for AudioStore (save, get, delete, cleanup)
4. Implement AudioStore
5. Write test for get_duration_ms

**Deliverables:** Audio stitching and file management with full test coverage.

---

### Phase 6: TTS Provider Abstraction
**Spec:** 03 (TTS Provider Layer)
**Tasks:**
1. Write tests for the TTSProvider ABC (verify it cannot be instantiated)
2. Implement TTSProvider ABC in `backend/src/providers/base.py`
3. Write tests for ProviderRegistry (register, get, list)
4. Implement ProviderRegistry
5. Implement ONE provider (start with OpenAI TTS -- simplest, no timing data):
   a. Write tests with mocked httpx responses
   b. Implement OpenAITTSProvider
6. Implement Google Cloud TTS provider:
   a. Write tests with mocked SDK
   b. Implement GoogleCloudTTSProvider
7. Implement Amazon Polly provider:
   a. Write tests with moto
   b. Implement AmazonPollyProvider
8. Implement ElevenLabs provider:
   a. Write tests with mocked httpx
   b. Implement ElevenLabsProvider

**Deliverables:** All four providers implemented and tested with mocked APIs.

**NOTE:** Implementing providers one at a time allows end-to-end testing with
each before moving to the next. Start with the simplest (OpenAI -- no word
timing) and progress to the most complex (Google -- SSML marking).

---

### Phase 7: Job Manager
**Spec:** 06 (Job Manager)
**Tasks:**
1. Write tests for JobStore (create, get, update, cleanup)
2. Implement JobStore
3. Write tests for JobManager.create_job
4. Write tests for JobManager.process_job (full lifecycle with mock provider)
5. Implement JobManager
6. Write tests for retry logic (rate limit retry, exhaustion)
7. Implement retry logic
8. Write tests for error handling during processing

**Deliverables:** Complete job lifecycle management with retry and error handling.

---

### Phase 8: API Layer
**Spec:** 05 (API Layer)
**Tasks:**
1. Write tests for GET /api/providers
2. Implement providers endpoint
3. Write tests for POST /api/voices
4. Implement voices endpoint
5. Write tests for POST /api/generate
6. Implement generate endpoint
7. Write tests for GET /api/generate/{job_id}/status
8. Implement status polling endpoint
9. Write tests for GET /api/audio/{job_id} and GET /api/audio/{job_id}/file
10. Implement audio endpoints
11. Write tests for GET/PUT /api/settings
12. Implement settings endpoints
13. Write tests for error handler (verify no key leakage)
14. Register error handlers and wire up the FastAPI app

**Deliverables:** Complete API layer. Backend is fully functional and testable
via curl/httpie.

---

### Phase 9: Frontend State Management
**Spec:** 08 (Frontend State Management)
**Tasks:**
1. Write tests for the reducer (every action type, state transitions)
2. Implement the reducer
3. Implement AppContext and AppProvider
4. Write tests for the useAppState hook

**Deliverables:** Working state management with full test coverage.

---

### Phase 10: Frontend API Client
**Spec:** 13 (API Client)
**Tasks:**
1. Set up MSW handlers for test mocking
2. Write tests for each apiClient method (success and error paths)
3. Implement the API client

**Deliverables:** Typed API client with MSW-based tests.

---

### Phase 11: Frontend Hooks
**Spec:** 10 (Playback and Highlighting)
**Tasks:**
1. Write tests for useAudioPlayback hook
2. Implement useAudioPlayback
3. Write tests for useHighlighting hook (binary search, edge cases)
4. Implement useHighlighting
5. Write tests for useGenerationPolling hook
6. Implement useGenerationPolling
7. Write tests for useProviders hook
8. Implement useProviders

**Deliverables:** All custom hooks implemented and tested.

---

### Phase 12: Frontend Components
**Spec:** 09 (Frontend Components)
**Tasks:**
1. Implement and test AppShell (two-panel layout, dark theme)
2. Implement and test ProviderSelector
3. Implement and test VoiceSelector
4. Implement and test SpeedControl
5. Implement and test GenerateButton
6. Implement and test TextInputArea
7. Implement and test ProgressIndicator
8. Implement and test AudioPlayer
9. Implement and test HighlightedTextView (most complex)
10. Implement and test SettingsPanel
11. Wire everything together in App.tsx

**Deliverables:** Complete UI.

---

### Phase 13: Integration and End-to-End
**Tasks:**
1. Start backend and frontend together
2. Manual smoke test with a real (or mocked) TTS provider
3. Test the full flow: select provider -> select voice -> paste text ->
   generate -> playback with highlighting -> download
4. Fix any integration issues
5. Test with chapter-length text (5,000+ words)
6. Test error scenarios (bad API key, rate limiting)

**Deliverables:** Working application.

---

### Phase 14: Polish (if time permits)
**Specs:** MRD P1 features
**Tasks:**
1. Cost estimation (FR-012) -- if implementing
2. Provider capability indicators (FR-013) -- should already be in place
3. Language/locale filtering for voice selection (FR-015) -- if implementing
4. Final UI polish and CSS refinement

## Dependency Graph

```
Phase 1 (Scaffolding)
  |
  v
Phase 2 (Models + Errors) ----> Phase 9 (Frontend State)
  |                                  |
  v                                  v
Phase 3 (Config)             Phase 10 (API Client)
  |                                  |
  v                                  v
Phase 4 (Text Processing)   Phase 11 (Hooks)
  |                                  |
  v                                  v
Phase 5 (Audio Processing)  Phase 12 (Components)
  |                                  |
  v                                  |
Phase 6 (Providers)                  |
  |                                  |
  v                                  |
Phase 7 (Job Manager)               |
  |                                  |
  v                                  |
Phase 8 (API Layer)                  |
  |                                  |
  +--------+--------+---------------+
           |
           v
     Phase 13 (Integration)
           |
           v
     Phase 14 (Polish)
```

Backend and frontend can be developed in parallel after Phase 2. The backend
path (Phases 3-8) and frontend path (Phases 9-12) converge at Phase 13.

## Notes for Developer

1. **TDD is mandatory.** Every implementation task starts with writing tests.
   See CLAUDE.md conventions.
2. Each phase should result in all tests passing before moving to the next.
3. The provider implementations (Phase 6) are the most likely to encounter
   surprises with real API behavior. Start with OpenAI TTS which has the
   simplest API and no timing data.
4. The HighlightedTextView component (Phase 12, step 9) is the most complex
   frontend component. Allow extra time for performance optimization.
5. If building backend and frontend in parallel, use MSW handlers as the
   frontend's "backend" until the real backend is ready. The API contract
   (spec 05) serves as the shared interface.
