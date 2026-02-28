# TDD: Written from spec 05-api-layer.md
# Tests for GET /api/providers endpoint

import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient


class TestProvidersEndpoint:
    """Tests for the GET /api/providers endpoint."""

    def _make_app(self, providers_list=None):
        """Create a test FastAPI app with mocked dependencies."""
        from src.main import app
        from src.api.schemas import ProviderInfo, ProviderName, ProviderCapabilities

        if providers_list is None:
            providers_list = [
                ProviderInfo(
                    name=ProviderName.GOOGLE,
                    display_name="Google Cloud TTS",
                    capabilities=ProviderCapabilities(
                        supports_speed_control=True,
                        supports_word_timing=True,
                        max_chunk_chars=4500,
                    ),
                    is_configured=True,
                ),
                ProviderInfo(
                    name=ProviderName.OPENAI,
                    display_name="OpenAI TTS",
                    capabilities=ProviderCapabilities(
                        supports_speed_control=True,
                        supports_word_timing=False,
                        max_chunk_chars=4000,
                    ),
                    is_configured=False,
                ),
            ]

        mock_registry = MagicMock()
        mock_registry.list_providers.return_value = providers_list
        app.state.provider_registry = mock_registry
        return TestClient(app)

    def test_providers_returns_200(self):
        client = self._make_app()
        resp = client.get("/api/providers")
        assert resp.status_code == 200

    def test_providers_returns_all_providers(self):
        client = self._make_app()
        resp = client.get("/api/providers")
        data = resp.json()
        assert "providers" in data
        assert len(data["providers"]) == 2

    def test_providers_include_capabilities(self):
        client = self._make_app()
        resp = client.get("/api/providers")
        data = resp.json()
        provider = data["providers"][0]
        assert "capabilities" in provider
        assert "supports_speed_control" in provider["capabilities"]

    def test_providers_include_configured_status(self):
        client = self._make_app()
        resp = client.get("/api/providers")
        data = resp.json()
        google = next(p for p in data["providers"] if p["name"] == "google")
        openai = next(p for p in data["providers"] if p["name"] == "openai")
        assert google["is_configured"] is True
        assert openai["is_configured"] is False

    def test_providers_empty_list(self):
        client = self._make_app(providers_list=[])
        resp = client.get("/api/providers")
        data = resp.json()
        assert data["providers"] == []
