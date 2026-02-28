"""
Tests for request ID middleware and structured logging.

Verifies that:
  - Every response includes an X-Request-ID header
  - Provided X-Request-ID headers are preserved
  - New UUIDs are generated when no header is sent
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestRequestIDMiddleware:
    """Tests for the RequestIDMiddleware."""

    def test_response_includes_request_id_header(self, client):
        """Every response should have an X-Request-ID header."""
        response = client.get("/api/health")
        assert "x-request-id" in response.headers

    def test_generated_request_id_is_valid_uuid(self, client):
        """When no X-Request-ID is provided, a valid UUID should be generated."""
        response = client.get("/api/health")
        request_id = response.headers["x-request-id"]
        # Should not raise ValueError
        parsed = uuid.UUID(request_id)
        assert str(parsed) == request_id

    def test_provided_request_id_is_preserved(self, client):
        """When X-Request-ID is provided, it should be echoed back."""
        custom_id = "my-custom-request-id-12345"
        response = client.get("/api/health", headers={"X-Request-ID": custom_id})
        assert response.headers["x-request-id"] == custom_id
