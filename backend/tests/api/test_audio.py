# TDD: Written from spec 05-api-layer.md
# Tests for GET /api/audio/{job_id} and GET /api/audio/{job_id}/file endpoints

import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient


class TestAudioMetadataEndpoint:
    """Tests for GET /api/audio/{job_id} endpoint."""

    def _make_app(self):
        from src.main import app
        from src.api.schemas import (
            AudioMetadataResponse,
            TimingData,
            WordTiming,
        )

        mock_metadata = AudioMetadataResponse(
            job_id="test-job-123",
            duration_ms=5000,
            format="mp3",
            size_bytes=50000,
            timing=TimingData(
                timing_type="word",
                words=[
                    WordTiming(word="Hello", start_ms=0, end_ms=300, start_char=0, end_char=5),
                ],
                sentences=None,
            ),
        )

        mock_manager = MagicMock()
        mock_manager.get_audio_metadata.return_value = mock_metadata
        app.state.job_manager = mock_manager
        return TestClient(app)

    def test_audio_metadata_returns_200(self):
        client = self._make_app()
        resp = client.get("/api/audio/test-job-123")
        assert resp.status_code == 200

    def test_audio_metadata_returns_timing_data(self):
        client = self._make_app()
        resp = client.get("/api/audio/test-job-123")
        data = resp.json()
        assert data["job_id"] == "test-job-123"
        assert data["duration_ms"] == 5000
        assert data["format"] == "mp3"
        assert data["timing"]["timing_type"] == "word"
        assert len(data["timing"]["words"]) == 1

    def test_audio_metadata_job_not_found(self):
        from src.main import app
        from src.errors import JobNotFoundError

        mock_manager = MagicMock()
        mock_manager.get_audio_metadata.side_effect = JobNotFoundError("bad-id")
        app.state.job_manager = mock_manager

        client = TestClient(app)
        resp = client.get("/api/audio/bad-id")
        assert resp.status_code == 404

    def test_audio_metadata_job_not_completed(self):
        from src.main import app
        from src.errors import JobNotCompletedError

        mock_manager = MagicMock()
        mock_manager.get_audio_metadata.side_effect = JobNotCompletedError(
            "test-job", "in_progress"
        )
        app.state.job_manager = mock_manager

        client = TestClient(app)
        resp = client.get("/api/audio/test-job")
        assert resp.status_code == 409
        assert resp.json()["error_code"] == "JOB_NOT_COMPLETED"


class TestAudioFileEndpoint:
    """Tests for GET /api/audio/{job_id}/file endpoint."""

    def _make_app(self, tmp_path):
        from src.main import app

        # Create a fake MP3 file
        audio_path = tmp_path / "test-job-123.mp3"
        audio_path.write_bytes(b"\xff\xfb\x90\x00" + b"\x00" * 1024)

        mock_manager = MagicMock()
        mock_manager.get_audio_file_path.return_value = str(audio_path)
        app.state.job_manager = mock_manager
        return TestClient(app)

    def test_audio_file_returns_200(self, tmp_path):
        client = self._make_app(tmp_path)
        resp = client.get("/api/audio/test-job-123/file")
        assert resp.status_code == 200

    def test_audio_file_content_type(self, tmp_path):
        client = self._make_app(tmp_path)
        resp = client.get("/api/audio/test-job-123/file")
        assert "audio/mpeg" in resp.headers.get("content-type", "")

    def test_audio_file_content_disposition(self, tmp_path):
        client = self._make_app(tmp_path)
        resp = client.get("/api/audio/test-job-123/file")
        disposition = resp.headers.get("content-disposition", "")
        assert "attachment" in disposition
        assert ".mp3" in disposition

    def test_audio_file_returns_bytes(self, tmp_path):
        client = self._make_app(tmp_path)
        resp = client.get("/api/audio/test-job-123/file")
        assert len(resp.content) > 0

    def test_audio_file_job_not_found(self):
        from src.main import app
        from src.errors import JobNotFoundError

        mock_manager = MagicMock()
        mock_manager.get_audio_file_path.side_effect = JobNotFoundError("bad-id")
        app.state.job_manager = mock_manager

        client = TestClient(app)
        resp = client.get("/api/audio/bad-id/file")
        assert resp.status_code == 404

    def test_audio_file_not_completed(self):
        from src.main import app
        from src.errors import JobNotCompletedError

        mock_manager = MagicMock()
        mock_manager.get_audio_file_path.side_effect = JobNotCompletedError(
            "test-job", "pending"
        )
        app.state.job_manager = mock_manager

        client = TestClient(app)
        resp = client.get("/api/audio/test-job/file")
        assert resp.status_code == 409
