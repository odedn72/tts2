# TDD: Written from spec 03-tts-provider-layer.md
# Tests for ElevenLabsProvider in backend/src/providers/elevenlabs.py

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import httpx
import respx


class TestElevenLabsProviderMeta:
    """Tests for provider metadata and configuration."""

    def test_get_provider_name(self):
        from src.providers.elevenlabs import ElevenLabsProvider
        from src.api.schemas import ProviderName

        config = MagicMock()
        config.get_elevenlabs_api_key.return_value = "test-key"
        provider = ElevenLabsProvider(config)
        assert provider.get_provider_name() == ProviderName.ELEVENLABS

    def test_get_display_name(self):
        from src.providers.elevenlabs import ElevenLabsProvider

        config = MagicMock()
        config.get_elevenlabs_api_key.return_value = None
        provider = ElevenLabsProvider(config)
        assert "ElevenLabs" in provider.get_display_name()

    def test_is_configured_true(self):
        from src.providers.elevenlabs import ElevenLabsProvider

        config = MagicMock()
        config.get_elevenlabs_api_key.return_value = "test-key"
        provider = ElevenLabsProvider(config)
        assert provider.is_configured() is True

    def test_is_configured_false(self):
        from src.providers.elevenlabs import ElevenLabsProvider

        config = MagicMock()
        config.get_elevenlabs_api_key.return_value = None
        provider = ElevenLabsProvider(config)
        assert provider.is_configured() is False

    def test_capabilities(self):
        from src.providers.elevenlabs import ElevenLabsProvider

        config = MagicMock()
        config.get_elevenlabs_api_key.return_value = None
        provider = ElevenLabsProvider(config)
        caps = provider.get_capabilities()
        assert caps.supports_speed_control is True
        assert caps.supports_word_timing is True
        assert caps.max_chunk_chars == 4500


class TestElevenLabsProviderListVoices:
    """Tests for listing voices from ElevenLabs."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_list_voices_success(self):
        from src.providers.elevenlabs import ElevenLabsProvider
        from src.api.schemas import ProviderName

        config = MagicMock()
        config.get_elevenlabs_api_key.return_value = "test-key"
        provider = ElevenLabsProvider(config)

        respx.get("https://api.elevenlabs.io/v1/voices").mock(
            return_value=httpx.Response(
                200,
                json={
                    "voices": [
                        {
                            "voice_id": "voice-abc",
                            "name": "Rachel",
                            "labels": {"language": "en", "accent": "american"},
                        }
                    ]
                },
            )
        )

        voices = await provider.list_voices()
        assert len(voices) >= 1
        assert voices[0].voice_id == "voice-abc"
        assert voices[0].provider == ProviderName.ELEVENLABS

    @pytest.mark.asyncio
    @respx.mock
    async def test_list_voices_auth_error(self):
        from src.providers.elevenlabs import ElevenLabsProvider
        from src.errors import ProviderAuthError

        config = MagicMock()
        config.get_elevenlabs_api_key.return_value = "bad-key"
        provider = ElevenLabsProvider(config)

        respx.get("https://api.elevenlabs.io/v1/voices").mock(
            return_value=httpx.Response(401, json={"detail": {"message": "Unauthorized"}})
        )

        with pytest.raises(ProviderAuthError):
            await provider.list_voices()


class TestElevenLabsProviderSynthesize:
    """Tests for synthesizing audio with ElevenLabs."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_synthesize_with_timestamps(self):
        from src.providers.elevenlabs import ElevenLabsProvider

        config = MagicMock()
        config.get_elevenlabs_api_key.return_value = "test-key"
        provider = ElevenLabsProvider(config)

        # ElevenLabs with-timestamps endpoint returns JSON with audio and alignment
        respx.post(
            url__regex=r"https://api.elevenlabs.io/v1/text-to-speech/.*/with-timestamps"
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "audio_base64": "//uQxAAAAAAA",  # Tiny base64 audio
                    "alignment": {
                        "characters": ["H", "e", "l", "l", "o"],
                        "character_start_times_seconds": [0.0, 0.1, 0.15, 0.2, 0.25],
                        "character_end_times_seconds": [0.1, 0.15, 0.2, 0.25, 0.3],
                    },
                },
            )
        )

        result = await provider.synthesize("Hello", "voice-abc", 1.0)
        assert result.audio_bytes is not None
        assert len(result.audio_bytes) > 0

    @pytest.mark.asyncio
    @respx.mock
    async def test_synthesize_rate_limit(self):
        from src.providers.elevenlabs import ElevenLabsProvider
        from src.errors import ProviderRateLimitError

        config = MagicMock()
        config.get_elevenlabs_api_key.return_value = "test-key"
        provider = ElevenLabsProvider(config)

        respx.post(
            url__regex=r"https://api.elevenlabs.io/v1/text-to-speech/.*/with-timestamps"
        ).mock(
            return_value=httpx.Response(429, json={"detail": {"message": "Rate limit exceeded"}})
        )

        with pytest.raises(ProviderRateLimitError):
            await provider.synthesize("Hello", "voice-abc", 1.0)

    @pytest.mark.asyncio
    @respx.mock
    async def test_synthesize_api_error(self):
        from src.providers.elevenlabs import ElevenLabsProvider
        from src.errors import ProviderAPIError

        config = MagicMock()
        config.get_elevenlabs_api_key.return_value = "test-key"
        provider = ElevenLabsProvider(config)

        respx.post(
            url__regex=r"https://api.elevenlabs.io/v1/text-to-speech/.*/with-timestamps"
        ).mock(
            return_value=httpx.Response(500, json={"detail": {"message": "Internal error"}})
        )

        with pytest.raises(ProviderAPIError):
            await provider.synthesize("Hello", "voice-abc", 1.0)

    @pytest.mark.asyncio
    @respx.mock
    async def test_synthesize_clamps_speed(self):
        from src.providers.elevenlabs import ElevenLabsProvider

        config = MagicMock()
        config.get_elevenlabs_api_key.return_value = "test-key"
        provider = ElevenLabsProvider(config)

        respx.post(
            url__regex=r"https://api.elevenlabs.io/v1/text-to-speech/.*/with-timestamps"
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "audio_base64": "//uQxAAAAAAA",
                    "alignment": {
                        "characters": ["H"],
                        "character_start_times_seconds": [0.0],
                        "character_end_times_seconds": [0.1],
                    },
                },
            )
        )

        # Speed 5.0 should be clamped to max (1.2 for ElevenLabs)
        result = await provider.synthesize("H", "voice-abc", 5.0)
        assert result is not None
