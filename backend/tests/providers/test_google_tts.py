# TDD: Written from spec 03-tts-provider-layer.md
# Tests for GoogleCloudTTSProvider in backend/src/providers/google_tts.py

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestGoogleCloudTTSProviderMeta:
    """Tests for provider metadata and configuration."""

    def test_get_provider_name(self):
        from src.providers.google_tts import GoogleCloudTTSProvider
        from src.api.schemas import ProviderName

        config = MagicMock()
        config.get_google_credentials_path.return_value = "/path/creds.json"
        provider = GoogleCloudTTSProvider(config)
        assert provider.get_provider_name() == ProviderName.GOOGLE

    def test_get_display_name(self):
        from src.providers.google_tts import GoogleCloudTTSProvider

        config = MagicMock()
        config.get_google_credentials_path.return_value = None
        provider = GoogleCloudTTSProvider(config)
        assert "Google" in provider.get_display_name()

    def test_is_configured_true(self):
        from src.providers.google_tts import GoogleCloudTTSProvider

        config = MagicMock()
        config.get_google_credentials_path.return_value = "/path/creds.json"
        provider = GoogleCloudTTSProvider(config)
        assert provider.is_configured() is True

    def test_is_configured_false(self):
        from src.providers.google_tts import GoogleCloudTTSProvider

        config = MagicMock()
        config.get_google_credentials_path.return_value = None
        provider = GoogleCloudTTSProvider(config)
        assert provider.is_configured() is False

    def test_capabilities(self):
        from src.providers.google_tts import GoogleCloudTTSProvider

        config = MagicMock()
        config.get_google_credentials_path.return_value = None
        provider = GoogleCloudTTSProvider(config)
        caps = provider.get_capabilities()
        assert caps.supports_speed_control is True
        assert caps.supports_word_timing is True
        assert caps.max_chunk_chars == 4500
        assert caps.min_speed == 0.25
        assert caps.max_speed == 4.0


class TestGoogleCloudTTSProviderListVoices:
    """Tests for listing voices from Google Cloud TTS."""

    @pytest.mark.asyncio
    async def test_list_voices_returns_voice_objects(self):
        from src.providers.google_tts import GoogleCloudTTSProvider
        from src.api.schemas import ProviderName

        config = MagicMock()
        config.get_google_credentials_path.return_value = "/path/creds.json"
        provider = GoogleCloudTTSProvider(config)

        # Mock the Google TTS client
        mock_voice = MagicMock()
        mock_voice.name = "en-US-Neural2-A"
        mock_voice.language_codes = ["en-US"]
        mock_voice.ssml_gender.name = "FEMALE"

        mock_client = AsyncMock()
        mock_client.list_voices.return_value = MagicMock(voices=[mock_voice])

        with patch.object(provider, "_get_client", return_value=mock_client):
            voices = await provider.list_voices()
            assert len(voices) >= 1
            assert voices[0].provider == ProviderName.GOOGLE
            assert voices[0].voice_id == "en-US-Neural2-A"

    @pytest.mark.asyncio
    async def test_list_voices_auth_error(self):
        from src.providers.google_tts import GoogleCloudTTSProvider
        from src.errors import ProviderAuthError

        config = MagicMock()
        config.get_google_credentials_path.return_value = "/bad/path.json"
        provider = GoogleCloudTTSProvider(config)

        mock_client = AsyncMock()
        mock_client.list_voices.side_effect = Exception("403 Forbidden")

        with patch.object(provider, "_get_client", return_value=mock_client):
            with pytest.raises(ProviderAuthError):
                await provider.list_voices()


class TestGoogleCloudTTSProviderSynthesize:
    """Tests for synthesizing audio with Google Cloud TTS."""

    @pytest.mark.asyncio
    async def test_synthesize_returns_audio_and_timings(self):
        from src.providers.google_tts import GoogleCloudTTSProvider

        config = MagicMock()
        config.get_google_credentials_path.return_value = "/path/creds.json"
        provider = GoogleCloudTTSProvider(config)

        mock_response = MagicMock()
        mock_response.audio_content = b"\xff\xfb\x90\x00" + b"\x00" * 512
        mock_response.timepoints = []

        mock_client = AsyncMock()
        mock_client.synthesize_speech.return_value = mock_response

        with patch.object(provider, "_get_client", return_value=mock_client):
            result = await provider.synthesize("Hello world", "en-US-Neural2-A", 1.0)
            assert result.audio_bytes is not None
            assert len(result.audio_bytes) > 0
            assert result.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_synthesize_clamps_speed(self):
        from src.providers.google_tts import GoogleCloudTTSProvider

        config = MagicMock()
        config.get_google_credentials_path.return_value = "/path/creds.json"
        provider = GoogleCloudTTSProvider(config)

        mock_response = MagicMock()
        mock_response.audio_content = b"\xff\xfb\x90\x00" + b"\x00" * 512
        mock_response.timepoints = []

        mock_client = AsyncMock()
        mock_client.synthesize_speech.return_value = mock_response

        with patch.object(provider, "_get_client", return_value=mock_client):
            # Speed of 10.0 should be clamped to 4.0 max, not error
            result = await provider.synthesize("Hello", "en-US-Neural2-A", 10.0)
            assert result is not None

    @pytest.mark.asyncio
    async def test_synthesize_api_error(self):
        from src.providers.google_tts import GoogleCloudTTSProvider
        from src.errors import ProviderAPIError

        config = MagicMock()
        config.get_google_credentials_path.return_value = "/path/creds.json"
        provider = GoogleCloudTTSProvider(config)

        mock_client = AsyncMock()
        mock_client.synthesize_speech.side_effect = Exception("API Error")

        with patch.object(provider, "_get_client", return_value=mock_client):
            with pytest.raises(ProviderAPIError):
                await provider.synthesize("Hello", "en-US-Neural2-A", 1.0)
