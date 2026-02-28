"""
Internal job data model for TTS generation.

GenerationJob is a plain Python dataclass (not Pydantic) that tracks the
state of an asynchronous TTS generation job.
"""

from dataclasses import dataclass, field
from datetime import datetime

from src.api.schemas import GenerationStatus, ProviderName, TimingData


@dataclass
class GenerationJob:
    """
    Internal job tracking object. Stored in-memory.

    This is NOT a Pydantic model -- it is a plain dataclass used
    internally by the job store and job manager.
    """

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
