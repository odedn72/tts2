# TDD: Written from spec 05-api-layer.md
# Tests for POST /api/voices endpoint

import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient


class TestVoicesEndpoint:
    """Tests for the POST /api/voices endpoint."""

    def _make_app(self, mock_provider=None):
        from src.main import app
        from src.api.schemas import ProviderName, ProviderCapabilities, Voice

        if mock_provider is None:
            mock_provider = MagicMock()
            mock_provider.get_provider_name.return_value = ProviderName.GOOGLE
            mock_provider.is_configured.return_value = True
            mock_provider.list_voices = AsyncMock(
                return_value=[
                    Voice(
                        voice_id="en-US-Neural2-A",
                        name="Neural2-A",
                        language_code="en-US",
                        language_name="English (US)",
                        gender="FEMALE",
                        provider=ProviderName.GOOGLE,
                    ),
                ]
            )

        mock_registry = MagicMock()
        mock_registry.get.return_value = mock_provider
        app.state.provider_registry = mock_registry
        return TestClient(app)

    def test_voices_returns_200(self):
        client = self._make_app()
        resp = client.post("/api/voices", json={"provider": "google"})
        assert resp.status_code == 200

    def test_voices_returns_voice_list(self):
        client = self._make_app()
        resp = client.post("/api/voices", json={"provider": "google"})
        data = resp.json()
        assert "voices" in data
        assert len(data["voices"]) == 1
        assert data["voices"][0]["voice_id"] == "en-US-Neural2-A"

    def test_voices_invalid_provider(self):
        from src.main import app
        from src.errors import ProviderNotFoundError

        mock_registry = MagicMock()
        mock_registry.get.side_effect = ProviderNotFoundError("invalid")
        app.state.provider_registry = mock_registry

        client = TestClient(app)
        resp = client.post("/api/voices", json={"provider": "invalid"})
        # Should return 400 with INVALID_PROVIDER
        assert resp.status_code == 400
        assert resp.json()["error_code"] == "INVALID_PROVIDER"

    def test_voices_provider_not_configured(self):
        from src.main import app
        from src.api.schemas import ProviderName

        mock_provider = MagicMock()
        mock_provider.is_configured.return_value = False

        mock_registry = MagicMock()
        mock_registry.get.return_value = mock_provider
        app.state.provider_registry = mock_registry

        client = TestClient(app)
        resp = client.post("/api/voices", json={"provider": "google"})
        assert resp.status_code == 400
        assert resp.json()["error_code"] == "PROVIDER_NOT_CONFIGURED"

    def test_voices_provider_api_error(self):
        from src.main import app
        from src.errors import ProviderAPIError

        mock_provider = MagicMock()
        mock_provider.is_configured.return_value = True
        mock_provider.list_voices = AsyncMock(side_effect=ProviderAPIError("google", "API failed"))

        mock_registry = MagicMock()
        mock_registry.get.return_value = mock_provider
        app.state.provider_registry = mock_registry

        client = TestClient(app)
        resp = client.post("/api/voices", json={"provider": "google"})
        assert resp.status_code == 502
        assert resp.json()["error_code"] == "PROVIDER_API_ERROR"
