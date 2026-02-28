# 06 - Job Manager

**Date:** 2026-02-28
**Status:** Draft

## Goal

Define the job lifecycle management system that coordinates text chunking,
provider synthesis calls, audio stitching, and progress tracking for
asynchronous TTS generation.

**MRD traceability:** FR-004 (audio generation), FR-011 (chunking and progress
indication), NFR-002 (progress feedback), NFR-006 (graceful error handling).

## Job Lifecycle

```
PENDING -----> IN_PROGRESS -----> COMPLETED
   |               |
   +-------+-------+
           |
           v
         FAILED
```

- **PENDING:** Job created, not yet started processing
- **IN_PROGRESS:** Chunks are being synthesized; progress is updated per chunk
- **COMPLETED:** All chunks synthesized, audio stitched, timing merged
- **FAILED:** An error occurred; error_message is set

## Job Store

```python
class JobStore:
    """
    In-memory storage for generation jobs.

    Thread-safe access via asyncio (single-threaded event loop).
    No database -- suitable for single-user local app (AD-3).
    """

    def __init__(self) -> None:
        self._jobs: dict[str, GenerationJob] = {}

    def create(self, job: GenerationJob) -> None:
        """Store a new job."""
        ...

    def get(self, job_id: str) -> GenerationJob:
        """
        Retrieve a job by ID.

        Raises:
            JobNotFoundError: If the job does not exist.
        """
        ...

    def update(self, job: GenerationJob) -> None:
        """Update an existing job in the store."""
        ...

    def list_jobs(self) -> list[GenerationJob]:
        """List all jobs (for potential future history feature, FR-016)."""
        ...

    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """
        Remove jobs older than max_age_hours and delete their audio files.
        Returns the number of jobs removed.
        """
        ...
```

## Job Manager

```python
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
        ...

    async def create_job(self, request: GenerateRequest) -> GenerationJob:
        """
        Create a new generation job and return it.

        Does NOT start processing. The caller should start the background
        task separately.

        Steps:
        1. Validate the provider is configured
        2. Get provider capabilities (max_chunk_chars)
        3. Chunk the text
        4. Create GenerationJob with PENDING status
        5. Store in job_store
        6. Return the job
        """
        ...

    async def process_job(self, job_id: str) -> None:
        """
        Process a generation job (runs as a background task).

        Steps:
        1. Retrieve job from store
        2. Set status to IN_PROGRESS
        3. Get the TTSProvider from the registry
        4. For each chunk:
           a. Call provider.synthesize(chunk.text, voice_id, speed)
           b. Collect audio_bytes and timing data
           c. Update job progress (completed_chunks / total_chunks)
           d. Store intermediate state
        5. Stitch all audio chunks into a single MP3
        6. Merge all timing data with offset adjustments
        7. Save the final MP3 to disk
        8. Set job status to COMPLETED with audio_file_path and timing_data
        9. On any error: set status to FAILED with error_message
        """
        ...

    def get_job_status(self, job_id: str) -> GenerationJob:
        """
        Get current job status.

        Raises:
            JobNotFoundError: If job does not exist.
        """
        ...

    def get_audio_file_path(self, job_id: str) -> str:
        """
        Get the path to the generated audio file.

        Raises:
            JobNotFoundError: If job does not exist.
            JobNotCompletedError: If job is not in COMPLETED status.
        """
        ...

    def get_audio_metadata(self, job_id: str) -> AudioMetadataResponse:
        """
        Get audio metadata and timing data for a completed job.

        Raises:
            JobNotFoundError: If job does not exist.
            JobNotCompletedError: If job is not in COMPLETED status.
        """
        ...
```

## Process Job Flow (Detailed)

```
process_job(job_id):
  |
  +-- job = job_store.get(job_id)
  +-- job.status = IN_PROGRESS
  +-- job_store.update(job)
  |
  +-- provider = provider_registry.get(job.provider)
  +-- capabilities = provider.get_capabilities()
  +-- chunks = chunker.chunk(job.text, capabilities.max_chunk_chars)
  |
  +-- job.total_chunks = len(chunks)
  +-- job_store.update(job)
  |
  +-- audio_parts: list[bytes] = []
  +-- timing_parts: list[list[WordTiming | SentenceTiming]] = []
  +-- durations: list[int] = []
  |
  +-- for chunk in chunks:
  |     result = await provider.synthesize(chunk.text, job.voice_id, job.speed)
  |     audio_parts.append(result.audio_bytes)
  |     if result.word_timings:
  |         timing_parts.append(result.word_timings)
  |     elif result.sentence_timings:
  |         timing_parts.append(result.sentence_timings)
  |     durations.append(result.duration_ms)
  |     job.completed_chunks += 1
  |     job.progress = job.completed_chunks / job.total_chunks
  |     job_store.update(job)
  |
  +-- final_audio = audio_stitcher.stitch(audio_parts)
  +-- audio_path = save_to_disk(final_audio, job.id)
  |
  +-- Merge timing data:
  |     if word-level timings available:
  |         merged = timing_normalizer.merge_word_timings(chunks, timing_parts, durations)
  |         timing_data = TimingData(timing_type="word", words=merged)
  |     else:
  |         merged = timing_normalizer.merge_sentence_timings(chunks, timing_parts, durations)
  |         OR estimate:
  |         merged = timing_normalizer.estimate_sentence_timings(job.text, sum(durations))
  |         timing_data = TimingData(timing_type="sentence", sentences=merged)
  |
  +-- job.audio_file_path = audio_path
  +-- job.timing_data = timing_data
  +-- job.status = COMPLETED
  +-- job.completed_at = now()
  +-- job_store.update(job)
  |
  +-- ON ERROR at any step:
        job.status = FAILED
        job.error_message = user_friendly_error_message(exception)
        job_store.update(job)
```

## Error Handling During Processing

| Failure | Behavior |
|---------|----------|
| Provider auth error | Job fails immediately with "Provider authentication failed" message |
| Provider rate limit on a chunk | Retry up to 3 times with exponential backoff (1s, 2s, 4s). If still failing, job fails. |
| Provider API error on a chunk | No retry. Job fails with the provider's error message (sanitized). |
| Audio stitching failure | Job fails with "Audio processing failed" message |
| Timing merge failure | Log warning, fall back to sentence estimation. Job still completes. |
| Unexpected exception | Job fails with "An unexpected error occurred" message. Log full traceback. |

## Retry Logic

```python
MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 1.0

async def synthesize_with_retry(
    provider: TTSProvider,
    text: str,
    voice_id: str,
    speed: float,
) -> SynthesisResult:
    """
    Call provider.synthesize with retry on rate limit errors.

    Only retries ProviderRateLimitError. All other errors propagate immediately.
    """
    for attempt in range(MAX_RETRIES + 1):
        try:
            return await provider.synthesize(text, voice_id, speed)
        except ProviderRateLimitError:
            if attempt == MAX_RETRIES:
                raise
            backoff = INITIAL_BACKOFF_SECONDS * (2 ** attempt)
            await asyncio.sleep(backoff)
```

## Audio File Storage

- Audio files stored in the directory specified by `AUDIO_STORAGE_DIR`
  environment variable (default: system temp directory / `tts-app-audio`)
- Filename pattern: `{job_id}.mp3`
- Files are temporary and cleaned up by `cleanup_old_jobs()`
- The cleanup method should be called periodically (e.g., on app startup)

## Dependencies

- `ProviderRegistry` (spec 03)
- `TextChunker` (spec 04)
- `TimingNormalizer` (spec 04)
- `AudioStitcher` (spec 07)
- `JobStore` (this spec)
- Error types (spec 11)

## Notes for Developer

1. The `process_job` method must catch ALL exceptions and set the job to FAILED.
   An uncaught exception in a background task would be silently lost.
2. Use `asyncio.create_task` in the API route handler to start `process_job`.
   Store a reference to the task to prevent garbage collection.
3. The job store does not need locking since all access is on the asyncio event
   loop (single-threaded). However, if `asyncio.to_thread` is used for blocking
   calls, ensure job store updates happen on the event loop.
4. Test the job manager with a mock provider that returns predictable results.
   Test the full lifecycle: create -> process -> poll -> completed.
5. Test error scenarios: provider failure on chunk 3 of 5, rate limit retry
   success after 2 attempts, rate limit retry exhaustion.
6. The cleanup method should be tested by creating old jobs with known
   timestamps and verifying they are removed.
7. Consider adding a maximum concurrent jobs limit (e.g., 1) to prevent
   resource exhaustion. For a single-user app, this is a minor concern but
   good practice.
