# 05 - API Layer

**Date:** 2026-02-28
**Status:** Draft

## Goal

Define the FastAPI REST API endpoints, request/response contracts, and routing
structure. This is the boundary between frontend and backend.

**MRD traceability:** FR-001 (providers), FR-002 (voices), FR-004 (generation),
FR-005/FR-008 (audio delivery), FR-009 (speed), FR-010 (settings), FR-011
(progress). NFR-004 (no key exposure), NFR-005 (localhost only), NFR-007
(minimal clicks).

## API Base Configuration

- Base URL: `http://127.0.0.1:8000`
- All endpoints prefixed with `/api`
- Content-Type: `application/json` (except audio download)
- Errors: Structured JSON with `error_code`, `message`, `details`
- Auth: None (single-user local app)
- CORS: Not needed when using Vite proxy; if needed, restrict to localhost only

## Endpoints

### GET /api/providers

List all registered TTS providers with capabilities and configuration status.

**Request:** None

**Response: 200 OK**
```json
{
  "providers": [
    {
      "name": "google",
      "display_name": "Google Cloud TTS",
      "capabilities": {
        "supports_speed_control": true,
        "supports_word_timing": true,
        "min_speed": 0.25,
        "max_speed": 4.0,
        "default_speed": 1.0,
        "max_chunk_chars": 4500
      },
      "is_configured": true
    },
    {
      "name": "openai",
      "display_name": "OpenAI TTS",
      "capabilities": {
        "supports_speed_control": true,
        "supports_word_timing": false,
        "min_speed": 0.25,
        "max_speed": 4.0,
        "default_speed": 1.0,
        "max_chunk_chars": 4000
      },
      "is_configured": false
    }
  ]
}
```

**Errors:** None expected (always returns the list).

---

### POST /api/voices

Fetch available voices for a specific provider.

**Request:**
```json
{
  "provider": "google"
}
```

**Response: 200 OK**
```json
{
  "provider": "google",
  "voices": [
    {
      "voice_id": "en-US-Neural2-A",
      "name": "Neural2-A",
      "language_code": "en-US",
      "language_name": "English (US)",
      "gender": "FEMALE",
      "provider": "google"
    }
  ]
}
```

**Errors:**
| Status | error_code | When |
|--------|-----------|------|
| 400 | `INVALID_PROVIDER` | Unknown provider name |
| 400 | `PROVIDER_NOT_CONFIGURED` | Provider has no API key set |
| 502 | `PROVIDER_API_ERROR` | Provider API call failed |

---

### POST /api/generate

Start an asynchronous TTS generation job.

**Request:**
```json
{
  "provider": "google",
  "voice_id": "en-US-Neural2-A",
  "text": "Chapter 1. It was a dark and stormy night...",
  "speed": 1.0
}
```

**Validation:**
- `text`: min 1 char, max 100,000 chars
- `speed`: 0.25 to 4.0 (will be clamped to provider range server-side)
- `provider`: must be a valid ProviderName
- `voice_id`: non-empty string

**Response: 202 Accepted**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending"
}
```

**Errors:**
| Status | error_code | When |
|--------|-----------|------|
| 400 | `VALIDATION_ERROR` | Invalid request body |
| 400 | `PROVIDER_NOT_CONFIGURED` | Provider has no API key |
| 400 | `TEXT_EMPTY` | Text is empty or whitespace only |

**Backend behavior:**
1. Validate the request
2. Create a `GenerationJob` in the job store
3. Start a background task (`asyncio.create_task` or FastAPI `BackgroundTasks`)
4. Return 202 immediately with the job_id

---

### GET /api/generate/{job_id}/status

Poll for generation job progress.

**Response: 200 OK**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "in_progress",
  "progress": 0.6,
  "total_chunks": 5,
  "completed_chunks": 3,
  "error_message": null
}
```

When status is `"completed"`:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 1.0,
  "total_chunks": 5,
  "completed_chunks": 5,
  "error_message": null
}
```

When status is `"failed"`:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failed",
  "progress": 0.4,
  "total_chunks": 5,
  "completed_chunks": 2,
  "error_message": "Provider API returned error: rate limit exceeded"
}
```

**Errors:**
| Status | error_code | When |
|--------|-----------|------|
| 404 | `JOB_NOT_FOUND` | No job with this ID exists |

---

### GET /api/audio/{job_id}

Download the generated audio file and timing metadata.

**Response: 200 OK**

This endpoint returns a JSON envelope containing audio metadata and timing data.
The actual audio bytes are served separately (see below).

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "duration_ms": 125000,
  "format": "mp3",
  "size_bytes": 1500000,
  "timing": {
    "timing_type": "word",
    "words": [
      {
        "word": "Chapter",
        "start_ms": 0,
        "end_ms": 450,
        "start_char": 0,
        "end_char": 7
      },
      {
        "word": "1.",
        "start_ms": 450,
        "end_ms": 700,
        "start_char": 8,
        "end_char": 10
      }
    ],
    "sentences": null
  }
}
```

**Errors:**
| Status | error_code | When |
|--------|-----------|------|
| 404 | `JOB_NOT_FOUND` | No job with this ID |
| 409 | `JOB_NOT_COMPLETED` | Job is not in completed status |

---

### GET /api/audio/{job_id}/file

Stream the actual MP3 audio file bytes.

**Response: 200 OK**
- Content-Type: `audio/mpeg`
- Content-Disposition: `attachment; filename="tts-{job_id}.mp3"`
- Body: raw MP3 bytes

This endpoint is used both for the `<audio>` element `src` attribute and for
the download button.

**Errors:**
| Status | error_code | When |
|--------|-----------|------|
| 404 | `JOB_NOT_FOUND` | No job with this ID |
| 409 | `JOB_NOT_COMPLETED` | Job is not in completed status |

---

### GET /api/settings

Get current provider configuration status.

**Response: 200 OK**
```json
{
  "providers": [
    { "provider": "google", "is_configured": true },
    { "provider": "amazon", "is_configured": false },
    { "provider": "elevenlabs", "is_configured": true },
    { "provider": "openai", "is_configured": false }
  ]
}
```

**NOTE:** This endpoint NEVER returns actual API key values (NFR-004).

---

### PUT /api/settings

Update a provider's API key. Key is stored in the runtime settings (in-memory
for this session, optionally persisted to a local config file).

**Request:**
```json
{
  "provider": "openai",
  "api_key": "sk-..."
}
```

**Response: 200 OK**
```json
{
  "provider": "openai",
  "is_configured": true
}
```

**Errors:**
| Status | error_code | When |
|--------|-----------|------|
| 400 | `VALIDATION_ERROR` | Missing or empty api_key |
| 400 | `INVALID_PROVIDER` | Unknown provider name |

## Error Response Format

All error responses use a consistent structure:

```json
{
  "error_code": "PROVIDER_API_ERROR",
  "message": "Google Cloud TTS API returned an error: quota exceeded",
  "details": {
    "provider": "google",
    "original_error": "Resource exhausted"
  }
}
```

The `details` field is optional and may contain additional context. It must
NEVER contain API keys, credentials, or stack traces.

## FastAPI Exception Handler

```python
from fastapi import Request
from fastapi.responses import JSONResponse

async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.http_status,
        content={
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details,
        },
    )
```

Register this handler for the base `AppError` class so all custom errors are
automatically formatted.

## Router Structure

```python
# api/router.py
from fastapi import APIRouter

api_router = APIRouter(prefix="/api")
api_router.include_router(providers_router)
api_router.include_router(voices_router)
api_router.include_router(generate_router)
api_router.include_router(audio_router)
api_router.include_router(settings_router)
```

## Dependencies (FastAPI Dependency Injection)

```python
# Inject the ProviderRegistry into route handlers
async def get_provider_registry() -> ProviderRegistry:
    return app.state.provider_registry

async def get_job_manager() -> JobManager:
    return app.state.job_manager
```

## Notes for Developer

1. Use FastAPI's `BackgroundTasks` or `asyncio.create_task` for the generation
   background task. `asyncio.create_task` is preferred since it runs
   concurrently without needing the response to complete first.
2. The `/api/audio/{job_id}/file` endpoint should use `FileResponse` or
   `StreamingResponse` to serve the MP3 file efficiently.
3. Add request validation middleware to log request sizes (useful for debugging
   large text payloads).
4. Bind uvicorn to `127.0.0.1` only -- never `0.0.0.0` (NFR-005).
5. CORS middleware is not strictly needed with Vite proxy. If added, restrict
   origins to `http://127.0.0.1:5173` (Vite dev server) and
   `http://localhost:5173`.
6. Test all endpoints with the FastAPI `TestClient`. Mock the provider registry
   and job manager via dependency overrides.
7. Validate that error responses never contain API keys by writing explicit
   tests for error paths.
