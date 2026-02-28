"""
Tests for the GET /api/health endpoint.

Verifies that the health check returns correct status, version,
and dependency information.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for GET /api/health."""

    def test_health_returns_200(self, client):
        """Health endpoint should always return 200."""
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_health_returns_version(self, client):
        """Response should include the application version."""
        response = client.get("/api/health")
        data = response.json()
        assert "version" in data
        assert data["version"] == "0.1.0"

    def test_health_returns_status(self, client):
        """Response should include an overall status field."""
        response = client.get("/api/health")
        data = response.json()
        assert "status" in data
        assert data["status"] in ("healthy", "degraded")

    def test_health_returns_ffmpeg_dependency(self, client):
        """Response should include ffmpeg dependency status."""
        response = client.get("/api/health")
        data = response.json()
        assert "dependencies" in data
        assert "ffmpeg" in data["dependencies"]
        ffmpeg = data["dependencies"]["ffmpeg"]
        assert "available" in ffmpeg
        assert isinstance(ffmpeg["available"], bool)

    def test_health_healthy_when_ffmpeg_present(self, client):
        """Status should be 'healthy' when ffmpeg is found."""
        with patch("src.api.health.shutil.which", return_value="/usr/bin/ffmpeg"):
            response = client.get("/api/health")
            data = response.json()
            assert data["status"] == "healthy"
            assert data["dependencies"]["ffmpeg"]["available"] is True
            assert data["dependencies"]["ffmpeg"]["path"] == "/usr/bin/ffmpeg"

    def test_health_degraded_when_ffmpeg_missing(self, client):
        """Status should be 'degraded' when ffmpeg is not found."""
        with patch("src.api.health.shutil.which", return_value=None):
            response = client.get("/api/health")
            data = response.json()
            assert data["status"] == "degraded"
            assert data["dependencies"]["ffmpeg"]["available"] is False
            assert data["dependencies"]["ffmpeg"]["path"] is None
