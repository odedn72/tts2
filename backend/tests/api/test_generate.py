# TDD: Written from spec 05-api-layer.md
# Tests for POST /api/generate and GET /api/generate/{job_id}/status endpoints

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from datetime import datetime


class TestGenerateEndpoint:
    """Tests for POST /api/generate endpoint."""

    def _make_app(self, job_id="test-job-123"):
        from src.main import app
        from src.jobs.models import GenerationJob
        from src.api.schemas import ProviderName, GenerationStatus

        mock_job = GenerationJob(
            id=job_id,
            provider=ProviderName.GOOGLE,
            voice_id="en-US-Neural2-A",
            text="Hello world",
            speed=1.0,
            status=GenerationStatus.PENDING,
            progress=0.0,
            total_chunks=1,
            completed_chunks=0,
            audio_file_path=None,
            timing_data=None,
            error_message=None,
            created_at=datetime.utcnow(),
            completed_at=None,
        )

        mock_manager = MagicMock()
        mock_manager.create_job = AsyncMock(return_value=mock_job)
        app.state.job_manager = mock_manager
        return TestClient(app)

    def test_generate_returns_202(self):
        client = self._make_app()
        resp = client.post(
            "/api/generate",
            json={
                "provider": "google",
                "voice_id": "en-US-Neural2-A",
                "text": "Hello world",
                "speed": 1.0,
            },
        )
        assert resp.status_code == 202

    def test_generate_returns_job_id(self):
        client = self._make_app()
        resp = client.post(
            "/api/generate",
            json={
                "provider": "google",
                "voice_id": "en-US-Neural2-A",
                "text": "Hello world",
                "speed": 1.0,
            },
        )
        data = resp.json()
        assert "job_id" in data
        assert data["job_id"] == "test-job-123"
        assert data["status"] == "pending"

    def test_generate_validation_error_empty_text(self):
        from src.main import app

        app.state.job_manager = MagicMock()
        client = TestClient(app)
        resp = client.post(
            "/api/generate",
            json={
                "provider": "google",
                "voice_id": "test",
                "text": "",
                "speed": 1.0,
            },
        )
        assert resp.status_code == 422 or resp.status_code == 400

    def test_generate_validation_error_invalid_speed(self):
        from src.main import app

        app.state.job_manager = MagicMock()
        client = TestClient(app)
        resp = client.post(
            "/api/generate",
            json={
                "provider": "google",
                "voice_id": "test",
                "text": "Hello",
                "speed": 10.0,
            },
        )
        assert resp.status_code == 422 or resp.status_code == 400

    def test_generate_provider_not_configured(self):
        from src.main import app
        from src.errors import ProviderNotConfiguredError

        mock_manager = MagicMock()
        mock_manager.create_job = AsyncMock(
            side_effect=ProviderNotConfiguredError("google")
        )
        app.state.job_manager = mock_manager

        client = TestClient(app)
        resp = client.post(
            "/api/generate",
            json={
                "provider": "google",
                "voice_id": "test",
                "text": "Hello world",
            },
        )
        assert resp.status_code == 400
        assert resp.json()["error_code"] == "PROVIDER_NOT_CONFIGURED"


class TestGenerateStatusEndpoint:
    """Tests for GET /api/generate/{job_id}/status endpoint."""

    def _make_app(self, job_status="in_progress", progress=0.6):
        from src.main import app
        from src.jobs.models import GenerationJob
        from src.api.schemas import ProviderName, GenerationStatus

        mock_job = GenerationJob(
            id="test-job-123",
            provider=ProviderName.GOOGLE,
            voice_id="en-US-Neural2-A",
            text="Hello world",
            speed=1.0,
            status=GenerationStatus(job_status),
            progress=progress,
            total_chunks=5,
            completed_chunks=3,
            audio_file_path=None,
            timing_data=None,
            error_message=None if job_status != "failed" else "Something went wrong",
            created_at=datetime.utcnow(),
            completed_at=None,
        )

        mock_manager = MagicMock()
        mock_manager.get_job_status.return_value = mock_job
        app.state.job_manager = mock_manager
        return TestClient(app)

    def test_status_returns_200(self):
        client = self._make_app()
        resp = client.get("/api/generate/test-job-123/status")
        assert resp.status_code == 200

    def test_status_returns_progress(self):
        client = self._make_app(job_status="in_progress", progress=0.6)
        resp = client.get("/api/generate/test-job-123/status")
        data = resp.json()
        assert data["status"] == "in_progress"
        assert data["progress"] == 0.6
        assert data["total_chunks"] == 5
        assert data["completed_chunks"] == 3

    def test_status_completed(self):
        client = self._make_app(job_status="completed", progress=1.0)
        resp = client.get("/api/generate/test-job-123/status")
        data = resp.json()
        assert data["status"] == "completed"

    def test_status_failed_includes_error(self):
        client = self._make_app(job_status="failed", progress=0.4)
        resp = client.get("/api/generate/test-job-123/status")
        data = resp.json()
        assert data["status"] == "failed"
        assert data["error_message"] is not None

    def test_status_job_not_found(self):
        from src.main import app
        from src.errors import JobNotFoundError

        mock_manager = MagicMock()
        mock_manager.get_job_status.side_effect = JobNotFoundError("bad-id")
        app.state.job_manager = mock_manager

        client = TestClient(app)
        resp = client.get("/api/generate/bad-id/status")
        assert resp.status_code == 404
        assert resp.json()["error_code"] == "JOB_NOT_FOUND"
