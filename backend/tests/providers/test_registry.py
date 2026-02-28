# TDD: Written from spec 03-tts-provider-layer.md
# Tests for ProviderRegistry in backend/src/providers/registry.py

import pytest
from unittest.mock import MagicMock, AsyncMock


def _make_mock_provider(name="google", display_name="Google Cloud TTS", configured=True):
    """Create a mock TTSProvider."""
    from src.api.schemas import ProviderName, ProviderCapabilities

    provider = MagicMock()
    provider.get_provider_name.return_value = ProviderName(name)
    provider.get_display_name.return_value = display_name
    provider.is_configured.return_value = configured
    provider.get_capabilities.return_value = ProviderCapabilities(
        supports_speed_control=True,
        supports_word_timing=True,
    )
    return provider


class TestProviderRegistry:
    """Tests for the ProviderRegistry class."""

    def test_register_provider(self):
        from src.providers.registry import ProviderRegistry
        from src.api.schemas import ProviderName

        registry = ProviderRegistry()
        mock_provider = _make_mock_provider("google")
        registry.register(mock_provider)
        result = registry.get(ProviderName.GOOGLE)
        assert result is mock_provider

    def test_get_unregistered_provider_raises(self):
        from src.providers.registry import ProviderRegistry
        from src.api.schemas import ProviderName
        from src.errors import ProviderNotFoundError

        registry = ProviderRegistry()
        with pytest.raises(ProviderNotFoundError):
            registry.get(ProviderName.OPENAI)

    def test_list_providers_returns_all(self):
        from src.providers.registry import ProviderRegistry

        registry = ProviderRegistry()
        registry.register(_make_mock_provider("google", "Google Cloud TTS", True))
        registry.register(_make_mock_provider("openai", "OpenAI TTS", False))

        providers = registry.list_providers()
        assert len(providers) == 2
        names = {p.name for p in providers}
        assert "google" in names
        assert "openai" in names

    def test_list_providers_includes_capabilities(self):
        from src.providers.registry import ProviderRegistry

        registry = ProviderRegistry()
        registry.register(_make_mock_provider("google"))
        providers = registry.list_providers()
        assert providers[0].capabilities is not None
        assert providers[0].capabilities.supports_speed_control is True

    def test_list_providers_includes_configured_status(self):
        from src.providers.registry import ProviderRegistry

        registry = ProviderRegistry()
        registry.register(_make_mock_provider("google", configured=True))
        registry.register(_make_mock_provider("openai", display_name="OpenAI TTS", configured=False))

        providers = registry.list_providers()
        google_info = next(p for p in providers if p.name == "google")
        openai_info = next(p for p in providers if p.name == "openai")
        assert google_info.is_configured is True
        assert openai_info.is_configured is False

    def test_get_configured_providers(self):
        from src.providers.registry import ProviderRegistry

        registry = ProviderRegistry()
        registry.register(_make_mock_provider("google", configured=True))
        registry.register(_make_mock_provider("openai", display_name="OpenAI TTS", configured=False))

        configured = registry.get_configured_providers()
        assert len(configured) == 1
        assert configured[0].name == "google"

    def test_empty_registry(self):
        from src.providers.registry import ProviderRegistry

        registry = ProviderRegistry()
        assert registry.list_providers() == []
        assert registry.get_configured_providers() == []

    def test_register_overwrites_same_name(self):
        from src.providers.registry import ProviderRegistry
        from src.api.schemas import ProviderName

        registry = ProviderRegistry()
        provider_v1 = _make_mock_provider("google", display_name="V1")
        provider_v2 = _make_mock_provider("google", display_name="V2")

        registry.register(provider_v1)
        registry.register(provider_v2)
        result = registry.get(ProviderName.GOOGLE)
        assert result is provider_v2
