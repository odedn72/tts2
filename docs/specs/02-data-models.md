# 02 - Data Models

**Date:** 2026-02-28
**Status:** Draft

## Goal

Define all shared data models used across the backend and their TypeScript
equivalents on the frontend. These models form the contract between components
and between frontend and backend.

**MRD traceability:** Models support FR-001 (providers), FR-002 (voices),
FR-004 (generation), FR-006/FR-007 (timing data), FR-009 (speed), FR-011
(progress), FR-013 (provider capabilities).

## Backend Models (Pydantic v2)

### Provider Models

```python
from enum import Enum
from pydantic import BaseModel, Field


class ProviderName(str, Enum):
    GOOGLE = "google"
    AMAZON = "amazon"
    ELEVENLABS = "elevenlabs"
    OPENAI = "openai"


class ProviderCapabilities(BaseModel):
    """Describes what features a provider supports. (FR-013)"""
    supports_speed_control: bool
    supports_word_timing: bool
    min_speed: float = 0.25
    max_speed: float = 4.0
    default_speed: float = 1.0
    max_chunk_chars: int = 5000  # Provider-specific chunk size limit


class ProviderInfo(BaseModel):
    """Public provider metadata returned to the frontend."""
    name: ProviderName
    display_name: str
    capabilities: ProviderCapabilities
    is_configured: bool  # True if API key/credentials are present
```

### Voice Models

```python
class Voice(BaseModel):
    """A single voice available from a provider. (FR-002)"""
    voice_id: str                   # Provider-specific voice identifier
    name: str                       # Human-readable name
    language_code: str              # e.g., "en-US"
    language_name: str              # e.g., "English (US)"
    gender: str | None = None       # "MALE", "FEMALE", "NEUTRAL", or None
    provider: ProviderName


class VoiceListResponse(BaseModel):
    """Response for the voices endpoint."""
    provider: ProviderName
    voices: list[Voice]
```

### Generation Models

```python
import uuid
from datetime import datetime


class GenerationStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class GenerateRequest(BaseModel):
    """Request body for starting TTS generation. (FR-004)"""
    provider: ProviderName
    voice_id: str
    text: str = Field(..., min_length=1, max_length=100_000)
    speed: float = Field(default=1.0, ge=0.25, le=4.0)


class GenerateResponse(BaseModel):
    """Immediate response after accepting a generation job."""
    job_id: str
    status: GenerationStatus


class JobStatusResponse(BaseModel):
    """Response for polling job status. (FR-011)"""
    job_id: str
    status: GenerationStatus
    progress: float              # 0.0 to 1.0
    total_chunks: int
    completed_chunks: int
    error_message: str | None = None
```

### Timing Models

```python
class WordTiming(BaseModel):
    """Timing data for a single word. (FR-006)"""
    word: str
    start_ms: int                # Milliseconds from start of audio
    end_ms: int                  # Milliseconds from start of audio
    start_char: int              # Character offset in original text
    end_char: int                # Character offset in original text


class SentenceTiming(BaseModel):
    """Timing data for a sentence. Used in fallback mode. (FR-007)"""
    sentence: str
    start_ms: int
    end_ms: int
    start_char: int
    end_char: int


class TimingData(BaseModel):
    """Normalized timing data returned with generated audio."""
    timing_type: str             # "word" or "sentence"
    words: list[WordTiming] | None = None
    sentences: list[SentenceTiming] | None = None
```

### Audio Response Models

```python
class AudioMetadataResponse(BaseModel):
    """Metadata about generated audio (returned with status or separately)."""
    job_id: str
    duration_ms: int
    format: str                  # "mp3"
    size_bytes: int
    timing: TimingData
```

### Settings Models

```python
class ProviderKeyStatus(BaseModel):
    """Status of a single provider's API key configuration. (FR-010)"""
    provider: ProviderName
    is_configured: bool
    # Never include the actual key value


class SettingsResponse(BaseModel):
    """Current settings returned to the frontend."""
    providers: list[ProviderKeyStatus]


class UpdateSettingsRequest(BaseModel):
    """Request to update provider API keys. (FR-010)"""
    provider: ProviderName
    api_key: str = Field(..., min_length=1)
```

### Job Model (Internal, not exposed via API)

```python
class GenerationJob:
    """Internal job tracking object. Stored in-memory."""
    id: str
    provider: ProviderName
    voice_id: str
    text: str
    speed: float
    status: GenerationStatus
    progress: float
    total_chunks: int
    completed_chunks: int
    audio_file_path: str | None
    timing_data: TimingData | None
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None
```

## Frontend Types (TypeScript)

```typescript
// types/provider.ts

export type ProviderName = "google" | "amazon" | "elevenlabs" | "openai";

export interface ProviderCapabilities {
  supports_speed_control: boolean;
  supports_word_timing: boolean;
  min_speed: number;
  max_speed: number;
  default_speed: number;
  max_chunk_chars: number;
}

export interface ProviderInfo {
  name: ProviderName;
  display_name: string;
  capabilities: ProviderCapabilities;
  is_configured: boolean;
}

export interface Voice {
  voice_id: string;
  name: string;
  language_code: string;
  language_name: string;
  gender: string | null;
  provider: ProviderName;
}
```

```typescript
// types/audio.ts

export type GenerationStatus =
  | "pending"
  | "in_progress"
  | "completed"
  | "failed";

export interface WordTiming {
  word: string;
  start_ms: number;
  end_ms: number;
  start_char: number;
  end_char: number;
}

export interface SentenceTiming {
  sentence: string;
  start_ms: number;
  end_ms: number;
  start_char: number;
  end_char: number;
}

export interface TimingData {
  timing_type: "word" | "sentence";
  words: WordTiming[] | null;
  sentences: SentenceTiming[] | null;
}

export interface AudioMetadata {
  job_id: string;
  duration_ms: number;
  format: string;
  size_bytes: number;
  timing: TimingData;
}
```

```typescript
// types/api.ts

import type { ProviderName, ProviderInfo, Voice } from "./provider";
import type { GenerationStatus, AudioMetadata } from "./audio";

export interface GenerateRequest {
  provider: ProviderName;
  voice_id: string;
  text: string;
  speed: number;
}

export interface GenerateResponse {
  job_id: string;
  status: GenerationStatus;
}

export interface JobStatusResponse {
  job_id: string;
  status: GenerationStatus;
  progress: number;
  total_chunks: number;
  completed_chunks: number;
  error_message: string | null;
}

export interface VoiceListResponse {
  provider: ProviderName;
  voices: Voice[];
}

export interface ProviderKeyStatus {
  provider: ProviderName;
  is_configured: boolean;
}

export interface SettingsResponse {
  providers: ProviderKeyStatus[];
}

export interface UpdateSettingsRequest {
  provider: ProviderName;
  api_key: string;
}

export interface ApiError {
  error_code: string;
  message: string;
  details: Record<string, unknown> | null;
}
```

## Notes for Developer

1. Backend Pydantic models live in `backend/src/api/schemas.py` (API-facing)
   and respective module files for internal models.
2. Frontend TypeScript types live in `frontend/src/types/`.
3. The `TimingData` model uses a discriminated union pattern -- `timing_type`
   tells the consumer which array to use. When `timing_type` is `"word"`,
   `words` is populated and `sentences` is null. When `timing_type` is
   `"sentence"`, `sentences` is populated and `words` is null.
4. `start_char` and `end_char` on timing entries are character offsets into the
   original input text. These are essential for the frontend highlighting logic
   to map timing events back to text positions.
5. The `GenerationJob` is an internal model and should NOT be a Pydantic model.
   It should be a plain Python dataclass or class with methods for state
   transitions.
6. All API responses should use Pydantic's `model_dump(mode="json")` for
   serialization to ensure proper enum handling.
