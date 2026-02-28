"""
Job lifecycle management for asynchronous TTS generation.

Coordinates text chunking, provider synthesis calls, audio stitching,
and progress tracking.
"""

import asyncio
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone

from src.api.schemas import (
    AudioMetadataResponse,
    GenerateRequest,
    GenerationStatus,
    TimingData,
)
from src.errors import (
    JobNotCompletedError,
    JobNotFoundError,
    ProviderNotConfiguredError,
    ProviderRateLimitError,
    sanitize_provider_error,
)
from src.jobs.models import GenerationJob
from src.processing.audio import AudioStitcher
from src.processing.chunker import TextChunker
from src.processing.timing import TimingNormalizer
from src.providers.base import TTSProvider
from src.providers.registry import ProviderRegistry

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 1.0


async def synthesize_with_retry(
    provider: TTSProvider,
    text: str,
    voice_id: str,
    speed: float,
):
    """
    Call provider.synthesize with retry on rate limit errors.

    Only retries ProviderRateLimitError. All other errors propagate immediately.
    """
    from src.providers.base import SynthesisResult

    for attempt in range(MAX_RETRIES + 1):
        try:
            return await provider.synthesize(text, voice_id, speed)
        except ProviderRateLimitError:
            if attempt == MAX_RETRIES:
                raise
            backoff = INITIAL_BACKOFF_SECONDS * (2 ** attempt)
            await asyncio.sleep(backoff)


class JobStore:
    """
    In-memory storage for generation jobs.

    Thread-safe access via asyncio (single-threaded event loop).
    No database -- suitable for single-user local app.
    """

    def __init__(self) -> None:
        self._jobs: dict[str, GenerationJob] = {}

    def create(self, job: GenerationJob) -> None:
        """Store a new job."""
        self._jobs[job.id] = job

    def get(self, job_id: str) -> GenerationJob:
        """
        Retrieve a job by ID.

        Raises:
            JobNotFoundError: If the job does not exist.
        """
        job = self._jobs.get(job_id)
        if job is None:
            raise JobNotFoundError(job_id)
        return job

    def update(self, job: GenerationJob) -> None:
        """Update an existing job in the store."""
        self._jobs[job.id] = job

    def list_jobs(self) -> list[GenerationJob]:
        """List all jobs."""
        return list(self._jobs.values())

    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """
        Remove jobs older than max_age_hours.

        Returns the number of jobs removed.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        to_remove = []
        for job_id, job in self._jobs.items():
            created = job.created_at
            # Handle naive datetimes (from tests or legacy code)
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            if created < cutoff:
                to_remove.append(job_id)
        for job_id in to_remove:
            del self._jobs[job_id]
        return len(to_remove)


class JobManager:
    """
    Orchestrates the TTS generation workflow.

    Dependencies (injected via constructor):
      - provider_registry: ProviderRegistry
      - chunker: TextChunker
      - timing_normalizer: TimingNormalizer
      - audio_stitcher: AudioStitcher
      - job_store: JobStore
      - audio_storage_dir: str (path for temp audio files)
    """

    def __init__(
        self,
        provider_registry: ProviderRegistry,
        chunker: TextChunker,
        timing_normalizer: TimingNormalizer,
        audio_stitcher: AudioStitcher,
        job_store: JobStore,
        audio_storage_dir: str,
    ) -> None:
        self._registry = provider_registry
        self._chunker = chunker
        self._timing_normalizer = timing_normalizer
        self._stitcher = audio_stitcher
        self._job_store = job_store
        self._audio_dir = audio_storage_dir

    async def create_job(self, request: GenerateRequest) -> GenerationJob:
        """
        Create a new generation job and return it.

        Does NOT start processing. The caller should start the background
        task separately.
        """
        # Validate provider is available and configured
        provider = self._registry.get(request.provider)
        if not provider.is_configured():
            raise ProviderNotConfiguredError(request.provider.value)

        # Get capabilities for chunking
        caps = provider.get_capabilities()
        chunks = self._chunker.chunk(request.text, caps.max_chunk_chars)

        # Create job
        job = GenerationJob(
            id=str(uuid.uuid4()),
            provider=request.provider,
            voice_id=request.voice_id,
            text=request.text,
            speed=request.speed,
            status=GenerationStatus.PENDING,
            progress=0.0,
            total_chunks=len(chunks),
            completed_chunks=0,
            audio_file_path=None,
            timing_data=None,
            error_message=None,
            created_at=datetime.now(timezone.utc),
            completed_at=None,
        )

        self._job_store.create(job)
        return job

    async def process_job(self, job_id: str) -> None:
        """
        Process a generation job (runs as a background task).

        Catches ALL exceptions and sets the job to FAILED on error.
        """
        job = self._job_store.get(job_id)

        try:
            job.status = GenerationStatus.IN_PROGRESS
            self._job_store.update(job)

            provider = self._registry.get(job.provider)
            caps = provider.get_capabilities()
            chunks = self._chunker.chunk(job.text, caps.max_chunk_chars)

            job.total_chunks = len(chunks)
            self._job_store.update(job)

            audio_parts: list[bytes] = []
            word_timing_parts: list[list] = []
            sentence_timing_parts: list[list] = []
            durations: list[int] = []
            has_word_timings = False
            has_sentence_timings = False

            for chunk in chunks:
                result = await synthesize_with_retry(
                    provider, chunk.text, job.voice_id, job.speed
                )
                audio_parts.append(result.audio_bytes)
                durations.append(result.duration_ms)

                if result.word_timings:
                    word_timing_parts.append(result.word_timings)
                    has_word_timings = True
                else:
                    word_timing_parts.append([])

                if result.sentence_timings:
                    sentence_timing_parts.append(result.sentence_timings)
                    has_sentence_timings = True
                else:
                    sentence_timing_parts.append([])

                job.completed_chunks += 1
                job.progress = job.completed_chunks / job.total_chunks
                self._job_store.update(job)

            # Stitch audio
            final_audio = self._stitcher.stitch(audio_parts)

            # Save to disk
            os.makedirs(self._audio_dir, exist_ok=True)
            audio_path = os.path.join(self._audio_dir, f"{job.id}.mp3")
            with open(audio_path, "wb") as f:
                f.write(final_audio.audio_bytes)

            # Merge timing data, accounting for silence gaps between chunks
            silence_ms = self._stitcher.silence_between_ms
            try:
                if has_word_timings:
                    merged_words = self._timing_normalizer.merge_word_timings(
                        chunks, word_timing_parts, durations, silence_ms
                    )
                    timing_data = TimingData(
                        timing_type="word", words=merged_words, sentences=None
                    )
                elif has_sentence_timings:
                    merged_sentences = self._timing_normalizer.merge_sentence_timings(
                        chunks, sentence_timing_parts, durations, silence_ms
                    )
                    timing_data = TimingData(
                        timing_type="sentence", words=None, sentences=merged_sentences
                    )
                else:
                    # Estimate sentence timing
                    estimated = self._timing_normalizer.estimate_sentence_timings(
                        job.text, final_audio.duration_ms
                    )
                    timing_data = TimingData(
                        timing_type="sentence", words=None, sentences=estimated
                    )
            except Exception as timing_exc:
                logger.warning("Timing merge failed, falling back to estimation: %s", timing_exc)
                estimated = self._timing_normalizer.estimate_sentence_timings(
                    job.text, final_audio.duration_ms
                )
                timing_data = TimingData(
                    timing_type="sentence", words=None, sentences=estimated
                )

            job.audio_file_path = os.path.abspath(audio_path)
            job.timing_data = timing_data
            job.status = GenerationStatus.COMPLETED
            job.progress = 1.0
            job.completed_at = datetime.now(timezone.utc)
            self._job_store.update(job)

        except Exception as exc:
            job.status = GenerationStatus.FAILED
            job.error_message = sanitize_provider_error(str(exc))
            self._job_store.update(job)
            logger.exception("Job %s failed: %s", job_id, exc)

    def get_job_status(self, job_id: str) -> GenerationJob:
        """
        Get current job status.

        Raises:
            JobNotFoundError: If job does not exist.
        """
        return self._job_store.get(job_id)

    def get_audio_file_path(self, job_id: str) -> str:
        """
        Get the path to the generated audio file.

        Raises:
            JobNotFoundError: If job does not exist.
            JobNotCompletedError: If job is not in COMPLETED status.
        """
        job = self._job_store.get(job_id)
        if job.status != GenerationStatus.COMPLETED:
            raise JobNotCompletedError(job_id, job.status.value)
        if not job.audio_file_path:
            raise JobNotCompletedError(job_id, job.status.value)
        return job.audio_file_path

    def get_audio_metadata(self, job_id: str) -> AudioMetadataResponse:
        """
        Get audio metadata and timing data for a completed job.

        Raises:
            JobNotFoundError: If job does not exist.
            JobNotCompletedError: If job is not in COMPLETED status.
        """
        job = self._job_store.get(job_id)
        if job.status != GenerationStatus.COMPLETED:
            raise JobNotCompletedError(job_id, job.status.value)

        # Get file size
        size_bytes = 0
        duration_ms = 0
        if job.audio_file_path and os.path.isfile(job.audio_file_path):
            size_bytes = os.path.getsize(job.audio_file_path)
            try:
                with open(job.audio_file_path, "rb") as f:
                    duration_ms = self._stitcher.get_duration_ms(f.read())
            except Exception:
                duration_ms = 0

        timing = job.timing_data or TimingData(
            timing_type="sentence", words=None, sentences=[]
        )

        return AudioMetadataResponse(
            job_id=job_id,
            duration_ms=duration_ms,
            format="mp3",
            size_bytes=size_bytes,
            timing=timing,
        )
