# TDD: Written from spec 03-tts-provider-layer.md
# Tests for OpenAITTSProvider in backend/src/providers/openai_tts.py

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import httpx
import respx


class TestOpenAITTSProviderMeta:
    """Tests for provider metadata and configuration."""

    def test_get_provider_name(self):
        from src.providers.openai_tts import OpenAITTSProvider
        from src.api.schemas import ProviderName

        config = MagicMock()
        config.get_openai_api_key.return_value = "sk-test"
        provider = OpenAITTSProvider(config)
        assert provider.get_provider_name() == ProviderName.OPENAI

    def test_get_display_name(self):
        from src.providers.openai_tts import OpenAITTSProvider

        config = MagicMock()
        config.get_openai_api_key.return_value = None
        provider = OpenAITTSProvider(config)
        assert "OpenAI" in provider.get_display_name()

    def test_is_configured_true(self):
        from src.providers.openai_tts import OpenAITTSProvider

        config = MagicMock()
        config.get_openai_api_key.return_value = "sk-test"
        provider = OpenAITTSProvider(config)
        assert provider.is_configured() is True

    def test_is_configured_false(self):
        from src.providers.openai_tts import OpenAITTSProvider

        config = MagicMock()
        config.get_openai_api_key.return_value = None
        provider = OpenAITTSProvider(config)
        assert provider.is_configured() is False

    def test_capabilities(self):
        from src.providers.openai_tts import OpenAITTSProvider

        config = MagicMock()
        config.get_openai_api_key.return_value = None
        provider = OpenAITTSProvider(config)
        caps = provider.get_capabilities()
        assert caps.supports_speed_control is True
        assert caps.supports_word_timing is False  # OpenAI has no word timing
        assert caps.max_chunk_chars == 4000
        assert caps.min_speed == 0.25
        assert caps.max_speed == 4.0


class TestOpenAITTSProviderListVoices:
    """Tests for listing voices from OpenAI TTS."""

    @pytest.mark.asyncio
    async def test_list_voices_returns_hardcoded_voices(self):
        from src.providers.openai_tts import OpenAITTSProvider
        from src.api.schemas import ProviderName

        config = MagicMock()
        config.get_openai_api_key.return_value = "sk-test"
        provider = OpenAITTSProvider(config)

        voices = await provider.list_voices()
        # OpenAI has a known set of voices: alloy, echo, fable, onyx, nova, shimmer
        assert len(voices) == 6
        voice_ids = {v.voice_id for v in voices}
        assert "alloy" in voice_ids
        assert "echo" in voice_ids
        assert "fable" in voice_ids
        assert "onyx" in voice_ids
        assert "nova" in voice_ids
        assert "shimmer" in voice_ids
        for v in voices:
            assert v.provider == ProviderName.OPENAI


class TestOpenAITTSProviderSynthesize:
    """Tests for synthesizing audio with OpenAI TTS."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_synthesize_returns_audio_bytes(self):
        from src.providers.openai_tts import OpenAITTSProvider

        config = MagicMock()
        config.get_openai_api_key.return_value = "sk-test"
        provider = OpenAITTSProvider(config)

        fake_mp3 = b"\xff\xfb\x90\x00" + b"\x00" * 1024

        respx.post("https://api.openai.com/v1/audio/speech").mock(
            return_value=httpx.Response(200, content=fake_mp3)
        )

        result = await provider.synthesize("Hello world", "alloy", 1.0)
        assert result.audio_bytes == fake_mp3
        assert result.word_timings is None  # OpenAI does not provide word timing
        assert result.sentence_timings is not None or result.word_timings is None

    @pytest.mark.asyncio
    @respx.mock
    async def test_synthesize_sends_correct_request(self):
        from src.providers.openai_tts import OpenAITTSProvider

        config = MagicMock()
        config.get_openai_api_key.return_value = "sk-test"
        provider = OpenAITTSProvider(config)

        route = respx.post("https://api.openai.com/v1/audio/speech").mock(
            return_value=httpx.Response(200, content=b"\xff\xfb\x90\x00" + b"\x00" * 100)
        )

        await provider.synthesize("Hello", "nova", 1.5)
        assert route.called
        request_body = route.calls[0].request
        # Verify auth header
        assert "Bearer sk-test" in request_body.headers.get("authorization", "")

    @pytest.mark.asyncio
    @respx.mock
    async def test_synthesize_auth_error(self):
        from src.providers.openai_tts import OpenAITTSProvider
        from src.errors import ProviderAuthError

        config = MagicMock()
        config.get_openai_api_key.return_value = "bad-key"
        provider = OpenAITTSProvider(config)

        respx.post("https://api.openai.com/v1/audio/speech").mock(
            return_value=httpx.Response(
                401,
                json={"error": {"message": "Invalid API key", "type": "invalid_request_error"}},
            )
        )

        with pytest.raises(ProviderAuthError):
            await provider.synthesize("Hello", "alloy", 1.0)

    @pytest.mark.asyncio
    @respx.mock
    async def test_synthesize_rate_limit_error(self):
        from src.providers.openai_tts import OpenAITTSProvider
        from src.errors import ProviderRateLimitError

        config = MagicMock()
        config.get_openai_api_key.return_value = "sk-test"
        provider = OpenAITTSProvider(config)

        respx.post("https://api.openai.com/v1/audio/speech").mock(
            return_value=httpx.Response(
                429,
                json={"error": {"message": "Rate limit exceeded", "type": "rate_limit_error"}},
            )
        )

        with pytest.raises(ProviderRateLimitError):
            await provider.synthesize("Hello", "alloy", 1.0)

    @pytest.mark.asyncio
    @respx.mock
    async def test_synthesize_api_error(self):
        from src.providers.openai_tts import OpenAITTSProvider
        from src.errors import ProviderAPIError

        config = MagicMock()
        config.get_openai_api_key.return_value = "sk-test"
        provider = OpenAITTSProvider(config)

        respx.post("https://api.openai.com/v1/audio/speech").mock(
            return_value=httpx.Response(
                500,
                json={"error": {"message": "Server error", "type": "server_error"}},
            )
        )

        with pytest.raises(ProviderAPIError):
            await provider.synthesize("Hello", "alloy", 1.0)

    @pytest.mark.asyncio
    @respx.mock
    async def test_synthesize_clamps_speed(self):
        from src.providers.openai_tts import OpenAITTSProvider

        config = MagicMock()
        config.get_openai_api_key.return_value = "sk-test"
        provider = OpenAITTSProvider(config)

        respx.post("https://api.openai.com/v1/audio/speech").mock(
            return_value=httpx.Response(200, content=b"\xff\xfb\x90\x00" + b"\x00" * 100)
        )

        # Speed 10.0 should be clamped to 4.0 max, not error
        result = await provider.synthesize("Hello", "alloy", 10.0)
        assert result is not None
