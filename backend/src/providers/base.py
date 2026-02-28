"""
Abstract base class for TTS providers and the SynthesisResult dataclass.

All TTS provider implementations must inherit from TTSProvider and
implement all abstract methods.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.api.schemas import (
    ProviderCapabilities,
    ProviderName,
    SentenceTiming,
    Voice,
    WordTiming,
)


@dataclass
class SynthesisResult:
    """Result of synthesizing a single chunk of text."""

    audio_bytes: bytes
    word_timings: list[WordTiming] | None
    sentence_timings: list[SentenceTiming] | None
    sample_rate: int
    duration_ms: int


class TTSProvider(ABC):
    """
    Abstract base class for all TTS providers.

    Each provider implementation must:
    1. Implement all abstract methods
    2. Handle its own authentication using provided config
    3. Return audio in MP3 format
    4. Return timing data in the normalized WordTiming/SentenceTiming format
    5. Raise TTSProviderError subclasses for all failures
    """

    @abstractmethod
    async def list_voices(self) -> list[Voice]:
        """
        Fetch available voices from the provider.

        Returns:
            List of Voice objects with voice_id, name, language, gender.

        Raises:
            ProviderAuthError: If credentials are invalid or missing.
            ProviderAPIError: If the API call fails.
        """
        ...

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice_id: str,
        speed: float = 1.0,
    ) -> SynthesisResult:
        """
        Convert a text chunk to speech.

        Args:
            text: Text to synthesize (already chunked, within provider limits).
            voice_id: The provider-specific voice identifier.
            speed: Speaking rate multiplier (1.0 = normal).

        Returns:
            SynthesisResult with audio bytes and timing data.

        Raises:
            ProviderAuthError: If credentials are invalid.
            ProviderAPIError: If synthesis fails.
            ProviderRateLimitError: If rate limited.
        """
        ...

    @abstractmethod
    def get_capabilities(self) -> ProviderCapabilities:
        """
        Return static capability metadata for this provider.

        This method is synchronous since capabilities are known statically.
        """
        ...

    @abstractmethod
    def is_configured(self) -> bool:
        """
        Check whether this provider has valid credentials configured.

        Returns True if API key / credentials are present (does not validate
        them against the API -- just checks if they are set).
        """
        ...

    @abstractmethod
    def get_provider_name(self) -> ProviderName:
        """Return the ProviderName enum value for this provider."""
        ...

    @abstractmethod
    def get_display_name(self) -> str:
        """Return a human-readable display name."""
        ...
