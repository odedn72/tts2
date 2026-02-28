"""
Pydantic v2 request/response models for the TTS Reader API.

These models form the contract between the frontend and backend,
and are used for validation, serialization, and documentation.
"""

from enum import Enum

from pydantic import BaseModel, Field


# --- Provider Models ---


class ProviderName(str, Enum):
    """Supported TTS provider identifiers."""

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
    max_chunk_chars: int = 5000


class ProviderInfo(BaseModel):
    """Public provider metadata returned to the frontend."""

    name: ProviderName
    display_name: str
    capabilities: ProviderCapabilities
    is_configured: bool


# --- Voice Models ---


class Voice(BaseModel):
    """A single voice available from a provider. (FR-002)"""

    voice_id: str
    name: str
    language_code: str
    language_name: str
    gender: str | None = None
    provider: ProviderName


class VoiceListResponse(BaseModel):
    """Response for the voices endpoint."""

    provider: ProviderName
    voices: list[Voice]


# --- Generation Models ---


class GenerationStatus(str, Enum):
    """Status of a TTS generation job."""

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
    progress: float
    total_chunks: int
    completed_chunks: int
    error_message: str | None = None


# --- Timing Models ---


class WordTiming(BaseModel):
    """Timing data for a single word. (FR-006)"""

    word: str
    start_ms: int
    end_ms: int
    start_char: int
    end_char: int


class SentenceTiming(BaseModel):
    """Timing data for a sentence. Used in fallback mode. (FR-007)"""

    sentence: str
    start_ms: int
    end_ms: int
    start_char: int
    end_char: int


class TimingData(BaseModel):
    """Normalized timing data returned with generated audio."""

    timing_type: str  # "word" or "sentence"
    words: list[WordTiming] | None = None
    sentences: list[SentenceTiming] | None = None


# --- Audio Response Models ---


class AudioMetadataResponse(BaseModel):
    """Metadata about generated audio (returned with status or separately)."""

    job_id: str
    duration_ms: int
    format: str  # "mp3"
    size_bytes: int
    timing: TimingData


# --- Settings Models ---


class ProviderKeyStatus(BaseModel):
    """Status of a single provider's API key configuration. (FR-010)"""

    provider: ProviderName
    is_configured: bool


class SettingsResponse(BaseModel):
    """Current settings returned to the frontend."""

    providers: list[ProviderKeyStatus]


class UpdateSettingsRequest(BaseModel):
    """Request to update provider API keys. (FR-010)"""

    provider: ProviderName
    api_key: str = Field(..., min_length=1)
