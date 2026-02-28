# TDD: Written from spec 05-api-layer.md
# Tests for GET /api/settings and PUT /api/settings endpoints

import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient


class TestGetSettingsEndpoint:
    """Tests for GET /api/settings endpoint."""

    def _make_app(self):
        from src.main import app
        from src.api.schemas import ProviderName

        mock_config = MagicMock()
        mock_config.is_provider_configured.side_effect = lambda p: p in (
            ProviderName.GOOGLE,
            ProviderName.ELEVENLABS,
        )
        app.state.runtime_config = mock_config

        # Mock registry with all 4 providers
        mock_registry = MagicMock()
        mock_provider_names = [
            ProviderName.GOOGLE,
            ProviderName.AMAZON,
            ProviderName.ELEVENLABS,
            ProviderName.OPENAI,
        ]
        app.state.provider_registry = mock_registry
        # Store provider names for the settings endpoint to iterate
        app.state._provider_names = mock_provider_names
        return TestClient(app)

    def test_settings_returns_200(self):
        client = self._make_app()
        resp = client.get("/api/settings")
        assert resp.status_code == 200

    def test_settings_returns_provider_statuses(self):
        client = self._make_app()
        resp = client.get("/api/settings")
        data = resp.json()
        assert "providers" in data
        assert len(data["providers"]) >= 1

    def test_settings_never_contains_api_keys(self):
        client = self._make_app()
        resp = client.get("/api/settings")
        data = resp.json()
        text = str(data)
        assert "api_key" not in text.lower() or "is_configured" in text
        # No field should contain actual key values
        for provider_status in data.get("providers", []):
            assert "api_key" not in provider_status
            assert "key" not in provider_status or provider_status.get("key") is None


class TestUpdateSettingsEndpoint:
    """Tests for PUT /api/settings endpoint."""

    def _make_app(self):
        from src.main import app

        mock_config = MagicMock()
        app.state.runtime_config = mock_config
        app.state.provider_registry = MagicMock()
        return TestClient(app)

    def test_update_settings_returns_200(self):
        client = self._make_app()
        resp = client.put(
            "/api/settings",
            json={"provider": "openai", "api_key": "sk-new-key"},
        )
        assert resp.status_code == 200

    def test_update_settings_returns_configured_status(self):
        client = self._make_app()
        resp = client.put(
            "/api/settings",
            json={"provider": "openai", "api_key": "sk-new-key"},
        )
        data = resp.json()
        assert data["provider"] == "openai"
        assert data["is_configured"] is True

    def test_update_settings_empty_key_rejected(self):
        client = self._make_app()
        resp = client.put(
            "/api/settings",
            json={"provider": "openai", "api_key": ""},
        )
        assert resp.status_code == 422 or resp.status_code == 400

    def test_update_settings_invalid_provider(self):
        client = self._make_app()
        resp = client.put(
            "/api/settings",
            json={"provider": "invalid_provider", "api_key": "key"},
        )
        assert resp.status_code == 422 or resp.status_code == 400

    def test_update_settings_response_never_echoes_key(self):
        client = self._make_app()
        resp = client.put(
            "/api/settings",
            json={"provider": "openai", "api_key": "sk-secret-key"},
        )
        data = resp.json()
        assert "sk-secret-key" not in str(data)


class TestErrorHandler:
    """Tests for the FastAPI error handler."""

    def test_app_error_returns_structured_json(self):
        from src.main import app
        from src.errors import JobNotFoundError

        mock_manager = MagicMock()
        mock_manager.get_job_status.side_effect = JobNotFoundError("test-id")
        app.state.job_manager = mock_manager

        client = TestClient(app)
        resp = client.get("/api/generate/test-id/status")
        data = resp.json()
        assert "error_code" in data
        assert "message" in data
        assert "details" in data

    def test_error_response_no_api_keys_leaked(self):
        from src.main import app
        from src.errors import ProviderAuthError

        mock_manager = MagicMock()
        mock_manager.get_job_status.side_effect = ProviderAuthError(
            "google", detail="key=sk-12345678901234567890"
        )
        app.state.job_manager = mock_manager

        client = TestClient(app)
        resp = client.get("/api/generate/test-id/status")
        text = resp.text
        # The 20+ char key should be redacted
        assert "sk-12345678901234567890" not in text

    def test_unhandled_error_returns_500(self):
        from src.main import app

        mock_manager = MagicMock()
        mock_manager.get_job_status.side_effect = RuntimeError("unexpected crash")
        app.state.job_manager = mock_manager

        client = TestClient(app)
        resp = client.get("/api/generate/test-id/status")
        assert resp.status_code == 500
        data = resp.json()
        assert data["error_code"] == "INTERNAL_ERROR"
        # Must not leak stack trace
        assert "RuntimeError" not in data["message"]
        assert "unexpected crash" not in data["message"]
