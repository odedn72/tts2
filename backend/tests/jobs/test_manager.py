# TDD: Written from spec 06-job-manager.md
# Tests for JobStore and JobManager in backend/src/jobs/manager.py

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timedelta


class TestJobStore:
    """Tests for the in-memory JobStore."""

    def _make_job(self, job_id="job-1", status="pending"):
        from src.jobs.models import GenerationJob
        from src.api.schemas import ProviderName, GenerationStatus

        return GenerationJob(
            id=job_id,
            provider=ProviderName.GOOGLE,
            voice_id="en-US-Neural2-A",
            text="Hello world",
            speed=1.0,
            status=GenerationStatus(status),
            progress=0.0,
            total_chunks=0,
            completed_chunks=0,
            audio_file_path=None,
            timing_data=None,
            error_message=None,
            created_at=datetime.utcnow(),
            completed_at=None,
        )

    def test_create_and_get_job(self):
        from src.jobs.manager import JobStore

        store = JobStore()
        job = self._make_job("job-1")
        store.create(job)
        retrieved = store.get("job-1")
        assert retrieved.id == "job-1"

    def test_get_nonexistent_job_raises(self):
        from src.jobs.manager import JobStore
        from src.errors import JobNotFoundError

        store = JobStore()
        with pytest.raises(JobNotFoundError):
            store.get("nonexistent")

    def test_update_job(self):
        from src.jobs.manager import JobStore
        from src.api.schemas import GenerationStatus

        store = JobStore()
        job = self._make_job("job-1")
        store.create(job)
        job.status = GenerationStatus.IN_PROGRESS
        job.progress = 0.5
        store.update(job)

        retrieved = store.get("job-1")
        assert retrieved.status == GenerationStatus.IN_PROGRESS
        assert retrieved.progress == 0.5

    def test_list_jobs(self):
        from src.jobs.manager import JobStore

        store = JobStore()
        store.create(self._make_job("job-1"))
        store.create(self._make_job("job-2"))
        jobs = store.list_jobs()
        assert len(jobs) == 2

    def test_list_jobs_empty(self):
        from src.jobs.manager import JobStore

        store = JobStore()
        assert store.list_jobs() == []

    def test_cleanup_old_jobs(self):
        from src.jobs.manager import JobStore

        store = JobStore()
        job = self._make_job("old-job")
        job.created_at = datetime.utcnow() - timedelta(hours=25)
        store.create(job)

        recent_job = self._make_job("recent-job")
        store.create(recent_job)

        removed = store.cleanup_old_jobs(max_age_hours=24)
        assert removed == 1
        assert len(store.list_jobs()) == 1


class TestJobManager:
    """Tests for the JobManager orchestration class."""

    def _make_manager(self, provider_mock=None, tmp_audio_dir="/tmp/test-audio"):
        from src.jobs.manager import JobManager, JobStore
        from src.processing.chunker import TextChunker
        from src.processing.timing import TimingNormalizer
        from src.processing.audio import AudioStitcher
        from src.providers.registry import ProviderRegistry

        registry = ProviderRegistry()
        if provider_mock:
            registry.register(provider_mock)

        return JobManager(
            provider_registry=registry,
            chunker=TextChunker(),
            timing_normalizer=TimingNormalizer(),
            audio_stitcher=AudioStitcher(),
            job_store=JobStore(),
            audio_storage_dir=tmp_audio_dir,
        )

    def _make_mock_provider(self, name="google"):
        from src.api.schemas import ProviderName, ProviderCapabilities, WordTiming
        from src.providers.base import SynthesisResult

        provider = MagicMock()
        provider.get_provider_name.return_value = ProviderName(name)
        provider.get_display_name.return_value = "Test Provider"
        provider.is_configured.return_value = True
        provider.get_capabilities.return_value = ProviderCapabilities(
            supports_speed_control=True,
            supports_word_timing=True,
            max_chunk_chars=5000,
        )

        # Create a tiny but valid MP3 for the mock
        from pydub.generators import Sine
        from io import BytesIO

        tone = Sine(440).to_audio_segment(duration=200)
        buf = BytesIO()
        tone.export(buf, format="mp3")
        mp3_bytes = buf.getvalue()

        provider.synthesize = AsyncMock(
            return_value=SynthesisResult(
                audio_bytes=mp3_bytes,
                word_timings=[
                    WordTiming(word="Hello", start_ms=0, end_ms=100, start_char=0, end_char=5),
                    WordTiming(word="world", start_ms=100, end_ms=200, start_char=6, end_char=11),
                ],
                sentence_timings=None,
                sample_rate=24000,
                duration_ms=200,
            )
        )
        return provider

    @pytest.mark.asyncio
    async def test_create_job(self, tmp_audio_dir):
        from src.api.schemas import GenerateRequest, ProviderName, GenerationStatus

        provider = self._make_mock_provider()
        manager = self._make_manager(provider, tmp_audio_dir)

        request = GenerateRequest(
            provider=ProviderName.GOOGLE,
            voice_id="en-US-Neural2-A",
            text="Hello world",
            speed=1.0,
        )
        job = await manager.create_job(request)
        assert job.id is not None
        assert job.status == GenerationStatus.PENDING
        assert job.provider == ProviderName.GOOGLE

    @pytest.mark.asyncio
    async def test_create_job_unconfigured_provider_raises(self, tmp_audio_dir):
        from src.api.schemas import GenerateRequest, ProviderName
        from src.errors import ProviderNotConfiguredError

        provider = self._make_mock_provider()
        provider.is_configured.return_value = False
        manager = self._make_manager(provider, tmp_audio_dir)

        request = GenerateRequest(
            provider=ProviderName.GOOGLE,
            voice_id="en-US-Neural2-A",
            text="Hello world",
        )
        with pytest.raises(ProviderNotConfiguredError):
            await manager.create_job(request)

    @pytest.mark.asyncio
    async def test_process_job_completes_successfully(self, tmp_audio_dir):
        from src.api.schemas import GenerateRequest, ProviderName, GenerationStatus

        provider = self._make_mock_provider()
        manager = self._make_manager(provider, tmp_audio_dir)

        request = GenerateRequest(
            provider=ProviderName.GOOGLE,
            voice_id="en-US-Neural2-A",
            text="Hello world",
        )
        job = await manager.create_job(request)
        await manager.process_job(job.id)

        completed_job = manager.get_job_status(job.id)
        assert completed_job.status == GenerationStatus.COMPLETED
        assert completed_job.progress == 1.0
        assert completed_job.audio_file_path is not None
        assert completed_job.timing_data is not None

    @pytest.mark.asyncio
    async def test_process_job_updates_progress(self, tmp_audio_dir):
        from src.api.schemas import GenerateRequest, ProviderName

        provider = self._make_mock_provider()
        manager = self._make_manager(provider, tmp_audio_dir)

        # Use longer text to get multiple chunks
        long_text = "Hello world. " * 500
        request = GenerateRequest(
            provider=ProviderName.GOOGLE,
            voice_id="en-US-Neural2-A",
            text=long_text,
        )
        job = await manager.create_job(request)
        await manager.process_job(job.id)

        completed = manager.get_job_status(job.id)
        assert completed.completed_chunks == completed.total_chunks

    @pytest.mark.asyncio
    async def test_process_job_provider_error_sets_failed(self, tmp_audio_dir):
        from src.api.schemas import GenerateRequest, ProviderName, GenerationStatus
        from src.errors import ProviderAPIError

        provider = self._make_mock_provider()
        provider.synthesize = AsyncMock(side_effect=ProviderAPIError("google", "API failed"))
        manager = self._make_manager(provider, tmp_audio_dir)

        request = GenerateRequest(
            provider=ProviderName.GOOGLE,
            voice_id="en-US-Neural2-A",
            text="Hello world",
        )
        job = await manager.create_job(request)
        await manager.process_job(job.id)

        failed_job = manager.get_job_status(job.id)
        assert failed_job.status == GenerationStatus.FAILED
        assert failed_job.error_message is not None

    @pytest.mark.asyncio
    async def test_process_job_auth_error_sets_failed(self, tmp_audio_dir):
        from src.api.schemas import GenerateRequest, ProviderName, GenerationStatus
        from src.errors import ProviderAuthError

        provider = self._make_mock_provider()
        provider.synthesize = AsyncMock(side_effect=ProviderAuthError("google"))
        manager = self._make_manager(provider, tmp_audio_dir)

        request = GenerateRequest(
            provider=ProviderName.GOOGLE,
            voice_id="en-US-Neural2-A",
            text="Hello world",
        )
        job = await manager.create_job(request)
        await manager.process_job(job.id)

        failed_job = manager.get_job_status(job.id)
        assert failed_job.status == GenerationStatus.FAILED

    def test_get_job_status_not_found(self, tmp_audio_dir):
        from src.errors import JobNotFoundError

        manager = self._make_manager(tmp_audio_dir=tmp_audio_dir)
        with pytest.raises(JobNotFoundError):
            manager.get_job_status("nonexistent")

    @pytest.mark.asyncio
    async def test_get_audio_file_path(self, tmp_audio_dir):
        from src.api.schemas import GenerateRequest, ProviderName

        provider = self._make_mock_provider()
        manager = self._make_manager(provider, tmp_audio_dir)

        request = GenerateRequest(
            provider=ProviderName.GOOGLE,
            voice_id="en-US-Neural2-A",
            text="Hello world",
        )
        job = await manager.create_job(request)
        await manager.process_job(job.id)

        path = manager.get_audio_file_path(job.id)
        assert path.endswith(".mp3")

    @pytest.mark.asyncio
    async def test_get_audio_file_path_not_completed_raises(self, tmp_audio_dir):
        from src.api.schemas import GenerateRequest, ProviderName
        from src.errors import JobNotCompletedError

        provider = self._make_mock_provider()
        manager = self._make_manager(provider, tmp_audio_dir)

        request = GenerateRequest(
            provider=ProviderName.GOOGLE,
            voice_id="en-US-Neural2-A",
            text="Hello world",
        )
        job = await manager.create_job(request)
        # Do NOT process the job
        with pytest.raises(JobNotCompletedError):
            manager.get_audio_file_path(job.id)

    @pytest.mark.asyncio
    async def test_get_audio_metadata(self, tmp_audio_dir):
        from src.api.schemas import GenerateRequest, ProviderName

        provider = self._make_mock_provider()
        manager = self._make_manager(provider, tmp_audio_dir)

        request = GenerateRequest(
            provider=ProviderName.GOOGLE,
            voice_id="en-US-Neural2-A",
            text="Hello world",
        )
        job = await manager.create_job(request)
        await manager.process_job(job.id)

        metadata = manager.get_audio_metadata(job.id)
        assert metadata.job_id == job.id
        assert metadata.format == "mp3"
        assert metadata.timing is not None


class TestRetryLogic:
    """Tests for the synthesis retry mechanism."""

    @pytest.mark.asyncio
    async def test_retry_succeeds_after_rate_limit(self):
        from src.jobs.manager import synthesize_with_retry
        from src.errors import ProviderRateLimitError
        from src.providers.base import SynthesisResult

        provider = MagicMock()
        result = SynthesisResult(
            audio_bytes=b"audio",
            word_timings=None,
            sentence_timings=None,
            sample_rate=24000,
            duration_ms=100,
        )
        # Fail twice with rate limit, succeed on third attempt
        provider.synthesize = AsyncMock(
            side_effect=[
                ProviderRateLimitError("test"),
                ProviderRateLimitError("test"),
                result,
            ]
        )

        with patch("src.jobs.manager.asyncio.sleep", new_callable=AsyncMock):
            got = await synthesize_with_retry(provider, "Hello", "voice", 1.0)
            assert got is result

    @pytest.mark.asyncio
    async def test_retry_exhausted_raises(self):
        from src.jobs.manager import synthesize_with_retry
        from src.errors import ProviderRateLimitError

        provider = MagicMock()
        provider.synthesize = AsyncMock(
            side_effect=ProviderRateLimitError("test"),
        )

        with patch("src.jobs.manager.asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(ProviderRateLimitError):
                await synthesize_with_retry(provider, "Hello", "voice", 1.0)

    @pytest.mark.asyncio
    async def test_retry_does_not_retry_non_rate_limit_errors(self):
        from src.jobs.manager import synthesize_with_retry
        from src.errors import ProviderAPIError

        provider = MagicMock()
        provider.synthesize = AsyncMock(
            side_effect=ProviderAPIError("test", "bad request"),
        )

        with pytest.raises(ProviderAPIError):
            await synthesize_with_retry(provider, "Hello", "voice", 1.0)

        # Should only be called once (no retries)
        assert provider.synthesize.call_count == 1
