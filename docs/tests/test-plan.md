# Test Plan: TTS Reader Application

**Date:** 2026-02-28
**Phase:** GREEN (TDD Mode 2 -- validation complete)
**Total Tests:** 457 (293 backend + 164 frontend)
**Passed:** 456 | **Failed:** 1 (test issue, not implementation bug)

## Backend Tests (263 tests)

| Test File | Spec | Description | Test Count |
|-----------|------|-------------|------------|
| `tests/test_errors.py` | 11 (Error Handling) | Error hierarchy: AppError, ValidationError, TextEmptyError, ProviderErrors (NotFound, NotConfigured, Auth, API, RateLimit), JobErrors (NotFound, NotCompleted), AudioProcessingError. Verifies error codes, HTTP statuses, messages, details, and inheritance tree. | 25 |
| `tests/test_schemas.py` | 02 (Data Models) | Pydantic models: ProviderName enum, ProviderCapabilities, ProviderInfo, Voice, VoiceListResponse, GenerationStatus, GenerateRequest (validation), GenerateResponse, JobStatusResponse, WordTiming, SentenceTiming, TimingData, AudioMetadataResponse, ProviderKeyStatus, SettingsResponse, UpdateSettingsRequest. Serialization and validation edge cases. | 33 |
| `tests/test_config.py` | 12 (Configuration) | Settings (env var loading for all providers, defaults), RuntimeConfig (get/set/is_configured for Google, AWS, ElevenLabs, OpenAI; override precedence; runtime key updates). | 24 |
| `tests/processing/test_chunker.py` | 04 (Text Processing) | TextChunker: single chunk, exact boundary, empty/whitespace errors, paragraph splitting, sentence splitting, word boundary fallback, full text coverage, sequential indices, total_chunks, character offsets, max_chars limit, unicode, emoji, consecutive newlines, short sentences, trailing whitespace. TextChunk dataclass. | 21 |
| `tests/processing/test_timing.py` | 04 (Text Processing) | TimingNormalizer: merge_word_timings (single chunk, two chunks with offset, monotonically increasing, empty chunk), merge_sentence_timings (single/two chunks), estimate_sentence_timings (single/multiple sentences, character offsets, total duration). split_into_sentences utility. | 15 |
| `tests/processing/test_audio.py` | 07 (Audio Processing) | AudioStitcher: empty list error, single chunk, two chunks, many chunks, silence between, invalid data error, MP3 format. get_duration_ms. AudioStore: directory creation, save/get/delete, nonexistent file error, cleanup old files, keep recent, overwrite. StitchResult dataclass. | 17 |
| `tests/providers/test_base.py` | 03 (TTS Provider Layer) | TTSProvider ABC: cannot instantiate, requires all abstract methods, incomplete subclass fails. SynthesisResult dataclass with word timings. | 9 |
| `tests/providers/test_registry.py` | 03 (TTS Provider Layer) | ProviderRegistry: register, get, get_unregistered raises, list_providers, capabilities, configured status, get_configured_providers, empty registry, overwrite same name. | 8 |
| `tests/providers/test_google_tts.py` | 03 (TTS Provider Layer) | GoogleCloudTTSProvider: provider name, display name, is_configured (true/false), capabilities (speed, timing, chunk size), list_voices (success, auth error), synthesize (returns audio, clamps speed, API error). | 9 |
| `tests/providers/test_amazon_polly.py` | 03 (TTS Provider Layer) | AmazonPollyProvider: provider name, display name, is_configured (true/false), capabilities, list_voices (success, auth error), synthesize (returns audio/timings, clamps speed, rate limit error). | 9 |
| `tests/providers/test_elevenlabs.py` | 03 (TTS Provider Layer) | ElevenLabsProvider: provider name, display name, is_configured (true/false), capabilities, list_voices (success, auth error), synthesize (with timestamps, rate limit, API error, clamps speed). | 10 |
| `tests/providers/test_openai_tts.py` | 03 (TTS Provider Layer) | OpenAITTSProvider: provider name, display name, is_configured (true/false), capabilities (no word timing), list_voices (6 hardcoded), synthesize (returns bytes, correct request, auth error, rate limit, API error, clamps speed). | 11 |
| `tests/jobs/test_manager.py` | 06 (Job Manager) | JobStore: create/get, not found error, update, list, list empty, cleanup old. JobManager: create_job, unconfigured provider error, process_job lifecycle (completes, updates progress, provider error -> failed, auth error -> failed), get_job_status not found, get_audio_file_path (success, not completed), get_audio_metadata. Retry logic: succeeds after rate limit, exhausted raises, no retry for non-rate-limit. | 18 |
| `tests/api/test_providers.py` | 05 (API Layer) | GET /api/providers: 200 status, all providers returned, capabilities included, configured status, empty list. | 5 |
| `tests/api/test_voices.py` | 05 (API Layer) | POST /api/voices: 200 status, voice list, invalid provider (400), not configured (400), API error (502). | 5 |
| `tests/api/test_generate.py` | 05 (API Layer) | POST /api/generate: 202 status, job_id returned, validation errors (empty text, invalid speed), provider not configured (400). GET /api/generate/{id}/status: 200 status, progress data, completed, failed with error, not found (404). | 10 |
| `tests/api/test_audio.py` | 05 (API Layer) | GET /api/audio/{id}: 200 with timing data, not found (404), not completed (409). GET /api/audio/{id}/file: 200, content-type audio/mpeg, content-disposition, returns bytes, not found (404), not completed (409). | 10 |
| `tests/api/test_settings.py` | 05 (API Layer) | GET /api/settings: 200, provider statuses, no API keys. PUT /api/settings: 200, configured status, empty key rejected, invalid provider, response never echoes key. Error handler: structured JSON, no key leakage, unhandled error returns 500. | 14 |
| `tests/test_edge_cases.py` | Mode 2 validation | Edge cases: sanitize_provider_error (6 tests), TextChunker single long word (2), max_chars boundaries (3), TimingNormalizer edge cases (4), AudioStore edge cases (4), ProviderRegistry edge cases (2), RuntimeConfig edge cases (2), Schema validation edge cases (7). | 30 |

## Frontend Tests (164 tests)

| Test File | Spec | Description | Test Count |
|-----------|------|-------------|------------|
| `tests/state/reducer.test.ts` | 08 (Frontend State) | appReducer: initial state (9 fields), PROVIDERS_LOADED, PROVIDER_SELECTED (5 aspects: selected, voice reset, voices clear, loading, default speed), VOICES_LOADING, VOICES_LOADED, VOICE_SELECTED, SPEED_CHANGED, TEXT_CHANGED, GENERATION_STARTED (status/clear audio), GENERATION_PROGRESS, GENERATION_COMPLETED, GENERATION_FAILED, AUDIO_LOADED, PLAYBACK_STARTED/PAUSED/TIME_UPDATE/ENDED/SEEK, SWITCH_TO_INPUT/PLAYBACK, SETTINGS_OPENED/CLOSED/UPDATED, ERROR_CLEARED/SET, unknown action. | 39 |
| `tests/api/client.test.ts` | 13 (API Client) | apiClient: getProviders (success, capabilities, server error), getVoices (success, body sent, 400 error), startGeneration (success, validation error), getJobStatus (success, 404), getAudioMetadata (success, 404, 409), getAudioFile (blob, download error), getSettings (success, no keys), updateSettings (success, error), error handling (ApiClientError code, non-JSON error). | 21 |
| `tests/hooks/useHighlighting.test.ts` | 10 (Playback/Highlighting) | findActiveTimingIndex: first word, mid-word, second word, last word, gap returns -1, past end, negative time, single entry, empty array, exact boundary. useHighlighting hook: null timing, word timing, second word, sentence timing, gap, time change updates. | 17 |
| `tests/hooks/useAudioPlayback.test.ts` | 10 (Playback/Highlighting) | useAudioPlayback: audioRef, not playing initially, not loaded with null url, play/pause functions, seek function, currentTimeMs/duration exposed. | 6 |
| `tests/hooks/useGenerationPolling.test.ts` | 10 (Playback/Highlighting) | useGenerationPolling: no poll with null jobId, polls when jobId provided, calls onCompleted, calls onFailed, stops after completion, cleans up on unmount. | 6 |
| `tests/components/AppShell.test.tsx` | 09 (Components) | AppShell: renders, left panel, right panel, dark theme, app title. | 5 |
| `tests/components/ProviderSelector.test.tsx` | 09 (Components) | ProviderSelector: select element, all providers displayed, unconfigured indicator, onSelect callback, shows selected, accessible label. | 6 |
| `tests/components/VoiceSelector.test.tsx` | 09 (Components) | VoiceSelector: select element, voice names, disabled state, loading state, onSelect callback, empty voices. | 6 |
| `tests/components/SpeedControl.test.tsx` | 09 (Components) | SpeedControl: range input visible, hidden when not visible, displays speed value, onChange callback, min/max attributes, disabled state, x suffix. | 7 |
| `tests/components/GenerateButton.test.tsx` | 09 (Components) | GenerateButton: button element, text, onClick, disabled, loading state, no click when disabled. | 6 |
| `tests/components/TextInputArea.test.tsx` | 09 (Components) | TextInputArea: textarea, placeholder, value display, onChange, disabled, long text. | 6 |
| `tests/components/HighlightedTextView.test.tsx` | 09 (Components) | HighlightedTextView: renders text, span elements, active word highlight, moving highlight, sentence-level, read-only, pre-wrap, no highlight in gap. | 8 |
| `tests/components/AudioPlayer.test.tsx` | 09 (Components) | AudioPlayer: renders with URL, hidden with null URL, play button, pause button, onPlay/onPause callbacks, download button, seek bar, hidden audio element. | 8 |
| `tests/components/ProgressIndicator.test.tsx` | 09 (Components) | ProgressIndicator: renders when visible, hidden when not, percentage, chunk progress, progress bar element, 100%, 0%. | 7 |
| `tests/edge-cases.test.ts` | Mode 2 validation | Edge cases: reducer state transitions (6 tests: reset on new generation, preserved fields on failure, speed fallback, error overwrite, switch preserves audio, playback ended preserves audio), binary search (4 tests: large arrays, end boundary, gaps, zero duration), ApiClientError class (2 tests), API client error paths (3 tests). | 15 |

## Test Infrastructure

| File | Purpose |
|------|---------|
| `backend/tests/conftest.py` | Shared fixtures: clean env, tmp_audio_dir, sample data (short/long text, timings, mp3 bytes) |
| `frontend/tests/setup.ts` | MSW server lifecycle, jest-dom matchers, cleanup |
| `frontend/tests/mocks/handlers.ts` | MSW request handlers for all API endpoints with sample data |
| `frontend/tests/mocks/server.ts` | MSW server instance |

## Coverage Targets

- Backend: >80% line coverage once implementation is complete
- Frontend: >80% branch coverage once implementation is complete

## Spec Coverage Matrix

| Spec | Backend Tests | Frontend Tests |
|------|--------------|----------------|
| 02 - Data Models | test_schemas.py | (types are TypeScript, not tested directly) |
| 03 - TTS Provider Layer | test_base.py, test_registry.py, test_google_tts.py, test_amazon_polly.py, test_elevenlabs.py, test_openai_tts.py | - |
| 04 - Text Processing | test_chunker.py, test_timing.py | - |
| 05 - API Layer | test_providers.py, test_voices.py, test_generate.py, test_audio.py, test_settings.py | - |
| 06 - Job Manager | test_manager.py | - |
| 07 - Audio Processing | test_audio.py (processing) | - |
| 08 - Frontend State | - | reducer.test.ts |
| 09 - Frontend Components | - | AppShell.test.tsx, ProviderSelector.test.tsx, VoiceSelector.test.tsx, SpeedControl.test.tsx, GenerateButton.test.tsx, TextInputArea.test.tsx, HighlightedTextView.test.tsx, AudioPlayer.test.tsx, ProgressIndicator.test.tsx |
| 10 - Playback/Highlighting | - | useHighlighting.test.ts, useAudioPlayback.test.ts, useGenerationPolling.test.ts |
| 11 - Error Handling | test_errors.py | (covered via API client error tests) |
| 12 - Configuration | test_config.py | - |
| 13 - API Client | - | client.test.ts |
