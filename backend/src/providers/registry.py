"""
Registry of all available TTS providers.

Dependency injection: providers are registered at app startup.
The registry does NOT instantiate providers -- they are passed in.
"""

from src.api.schemas import ProviderCapabilities, ProviderInfo, ProviderName
from src.errors import ProviderNotFoundError
from src.providers.base import TTSProvider


class ProviderRegistry:
    """
    Registry of all available TTS providers.

    Providers are registered at startup and can be looked up by name.
    """

    def __init__(self) -> None:
        self._providers: dict[ProviderName, TTSProvider] = {}

    def register(self, provider: TTSProvider) -> None:
        """Register a provider instance."""
        self._providers[provider.get_provider_name()] = provider

    def get(self, name: ProviderName) -> TTSProvider:
        """
        Get a provider by name.

        Raises:
            ProviderNotFoundError: If the provider is not registered.
        """
        provider = self._providers.get(name)
        if provider is None:
            raise ProviderNotFoundError(name.value if isinstance(name, ProviderName) else str(name))
        return provider

    def list_providers(self) -> list[ProviderInfo]:
        """
        List all registered providers with their capabilities and
        configuration status.
        """
        result: list[ProviderInfo] = []
        for provider in self._providers.values():
            result.append(
                ProviderInfo(
                    name=provider.get_provider_name(),
                    display_name=provider.get_display_name(),
                    capabilities=provider.get_capabilities(),
                    is_configured=provider.is_configured(),
                )
            )
        return result

    def get_configured_providers(self) -> list[ProviderInfo]:
        """List only providers that have credentials configured."""
        return [p for p in self.list_providers() if p.is_configured]
