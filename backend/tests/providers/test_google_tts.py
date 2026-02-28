# TDD: Written from spec 03-tts-provider-layer.md
# Tests for GoogleCloudTTSProvider in backend/src/providers/google_tts.py

import base64

import httpx
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _make_config(credentials_path=None, api_key=None):
    """Helper to create a mock RuntimeConfig."""
    config = MagicMock()
    config.get_google_credentials_path.return_value = credentials_path
    config.get_google_api_key.return_value = api_key
    return config


class TestGoogleCloudTTSProviderMeta:
    """Tests for provider metadata and configuration."""

    def test_get_provider_name(self):
        from src.providers.google_tts import GoogleCloudTTSProvider
        from src.api.schemas import ProviderName

        provider = GoogleCloudTTSProvider(_make_config(credentials_path="/path/creds.json"))
        assert provider.get_provider_name() == ProviderName.GOOGLE

    def test_get_display_name(self):
        from src.providers.google_tts import GoogleCloudTTSProvider

        provider = GoogleCloudTTSProvider(_make_config())
        assert "Google" in provider.get_display_name()

    def test_is_configured_true_with_credentials_path(self):
        from src.providers.google_tts import GoogleCloudTTSProvider

        provider = GoogleCloudTTSProvider(_make_config(credentials_path="/path/creds.json"))
        assert provider.is_configured() is True

    def test_is_configured_true_with_api_key(self):
        from src.providers.google_tts import GoogleCloudTTSProvider

        provider = GoogleCloudTTSProvider(_make_config(api_key="AIza-test-key"))
        assert provider.is_configured() is True

    def test_is_configured_true_with_both(self):
        from src.providers.google_tts import GoogleCloudTTSProvider

        provider = GoogleCloudTTSProvider(
            _make_config(credentials_path="/path/creds.json", api_key="AIza-test-key")
        )
        assert provider.is_configured() is True

    def test_is_configured_false(self):
        from src.providers.google_tts import GoogleCloudTTSProvider

        provider = GoogleCloudTTSProvider(_make_config())
        assert provider.is_configured() is False

    def test_capabilities(self):
        from src.providers.google_tts import GoogleCloudTTSProvider

        provider = GoogleCloudTTSProvider(_make_config())
        caps = provider.get_capabilities()
        assert caps.supports_speed_control is True
        assert caps.supports_word_timing is True
        assert caps.max_chunk_chars == 4500
        assert caps.min_speed == 0.25
        assert caps.max_speed == 4.0

    def test_use_rest_api_true_when_api_key_set(self):
        from src.providers.google_tts import GoogleCloudTTSProvider

        provider = GoogleCloudTTSProvider(_make_config(api_key="AIza-test-key"))
        assert provider._use_rest_api() is True

    def test_use_rest_api_false_when_no_api_key(self):
        from src.providers.google_tts import GoogleCloudTTSProvider

        provider = GoogleCloudTTSProvider(_make_config(credentials_path="/path/creds.json"))
        assert provider._use_rest_api() is False

    def test_api_key_takes_priority_over_credentials(self):
        from src.providers.google_tts import GoogleCloudTTSProvider

        provider = GoogleCloudTTSProvider(
            _make_config(credentials_path="/path/creds.json", api_key="AIza-test-key")
        )
        assert provider._use_rest_api() is True


class TestGoogleCloudTTSProviderListVoicesGRPC:
    """Tests for listing voices via gRPC (service account path)."""

    @pytest.mark.asyncio
    async def test_list_voices_returns_voice_objects(self):
        from src.providers.google_tts import GoogleCloudTTSProvider
        from src.api.schemas import ProviderName

        provider = GoogleCloudTTSProvider(_make_config(credentials_path="/path/creds.json"))

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

        provider = GoogleCloudTTSProvider(_make_config(credentials_path="/bad/path.json"))

        mock_client = AsyncMock()
        mock_client.list_voices.side_effect = Exception("403 Forbidden")

        with patch.object(provider, "_get_client", return_value=mock_client):
            with pytest.raises(ProviderAuthError):
                await provider.list_voices()


class TestGoogleCloudTTSProviderSynthesizeGRPC:
    """Tests for synthesizing audio via gRPC (service account path)."""

    @pytest.mark.asyncio
    async def test_synthesize_returns_audio_and_timings(self):
        from src.providers.google_tts import GoogleCloudTTSProvider

        provider = GoogleCloudTTSProvider(_make_config(credentials_path="/path/creds.json"))

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

        provider = GoogleCloudTTSProvider(_make_config(credentials_path="/path/creds.json"))

        mock_response = MagicMock()
        mock_response.audio_content = b"\xff\xfb\x90\x00" + b"\x00" * 512
        mock_response.timepoints = []

        mock_client = AsyncMock()
        mock_client.synthesize_speech.return_value = mock_response

        with patch.object(provider, "_get_client", return_value=mock_client):
            result = await provider.synthesize("Hello", "en-US-Neural2-A", 10.0)
            assert result is not None

    @pytest.mark.asyncio
    async def test_synthesize_api_error(self):
        from src.providers.google_tts import GoogleCloudTTSProvider
        from src.errors import ProviderAPIError

        provider = GoogleCloudTTSProvider(_make_config(credentials_path="/path/creds.json"))

        mock_client = AsyncMock()
        mock_client.synthesize_speech.side_effect = Exception("API Error")

        with patch.object(provider, "_get_client", return_value=mock_client):
            with pytest.raises(ProviderAPIError):
                await provider.synthesize("Hello", "en-US-Neural2-A", 1.0)


class TestGoogleCloudTTSProviderListVoicesREST:
    """Tests for listing voices via REST API (API key path)."""

    @pytest.mark.asyncio
    async def test_list_voices_rest_returns_voices(self):
        from src.providers.google_tts import GoogleCloudTTSProvider
        from src.api.schemas import ProviderName

        provider = GoogleCloudTTSProvider(_make_config(api_key="AIza-test-key"))

        mock_response = httpx.Response(
            200,
            json={
                "voices": [
                    {
                        "name": "en-US-Neural2-A",
                        "languageCodes": ["en-US"],
                        "ssmlGender": "FEMALE",
                        "naturalSampleRateHertz": 24000,
                    },
                    {
                        "name": "en-US-Neural2-C",
                        "languageCodes": ["en-US"],
                        "ssmlGender": "MALE",
                        "naturalSampleRateHertz": 24000,
                    },
                ]
            },
        )

        provider._http_client = AsyncMock()
        provider._http_client.get = AsyncMock(return_value=mock_response)

        voices = await provider.list_voices()
        assert len(voices) == 2
        assert voices[0].voice_id == "en-US-Neural2-A"
        assert voices[0].provider == ProviderName.GOOGLE
        assert voices[0].gender == "FEMALE"
        assert voices[1].voice_id == "en-US-Neural2-C"

    @pytest.mark.asyncio
    async def test_list_voices_rest_passes_api_key_header(self):
        from src.providers.google_tts import GoogleCloudTTSProvider

        provider = GoogleCloudTTSProvider(_make_config(api_key="AIza-test-key"))

        mock_response = httpx.Response(200, json={"voices": []})

        provider._http_client = AsyncMock()
        provider._http_client.get = AsyncMock(return_value=mock_response)

        await provider.list_voices()
        provider._http_client.get.assert_called_once()
        call_kwargs = provider._http_client.get.call_args
        assert call_kwargs.kwargs["headers"]["X-Goog-Api-Key"] == "AIza-test-key"

    @pytest.mark.asyncio
    async def test_list_voices_rest_auth_error(self):
        from src.providers.google_tts import GoogleCloudTTSProvider
        from src.errors import ProviderAuthError

        provider = GoogleCloudTTSProvider(_make_config(api_key="bad-key"))

        mock_response = httpx.Response(403, json={"error": {"message": "Forbidden"}})

        provider._http_client = AsyncMock()
        provider._http_client.get = AsyncMock(return_value=mock_response)

        with pytest.raises(ProviderAuthError):
            await provider.list_voices()

    @pytest.mark.asyncio
    async def test_list_voices_rest_api_error(self):
        from src.providers.google_tts import GoogleCloudTTSProvider
        from src.errors import ProviderAPIError

        provider = GoogleCloudTTSProvider(_make_config(api_key="AIza-test-key"))

        mock_response = httpx.Response(500, json={"error": {"message": "Internal error"}})

        provider._http_client = AsyncMock()
        provider._http_client.get = AsyncMock(return_value=mock_response)

        with pytest.raises(ProviderAPIError):
            await provider.list_voices()

    @pytest.mark.asyncio
    async def test_list_voices_rest_caches_results(self):
        from src.providers.google_tts import GoogleCloudTTSProvider

        provider = GoogleCloudTTSProvider(_make_config(api_key="AIza-test-key"))

        mock_response = httpx.Response(
            200,
            json={"voices": [{"name": "en-US-Neural2-A", "languageCodes": ["en-US"]}]},
        )

        provider._http_client = AsyncMock()
        provider._http_client.get = AsyncMock(return_value=mock_response)

        voices1 = await provider.list_voices()
        voices2 = await provider.list_voices()
        assert voices1 == voices2
        assert provider._http_client.get.call_count == 1

    @pytest.mark.asyncio
    async def test_list_voices_rest_multi_language(self):
        from src.providers.google_tts import GoogleCloudTTSProvider

        provider = GoogleCloudTTSProvider(_make_config(api_key="AIza-test-key"))

        mock_response = httpx.Response(
            200,
            json={
                "voices": [
                    {
                        "name": "de-DE-Neural2-A",
                        "languageCodes": ["de-DE"],
                        "ssmlGender": "FEMALE",
                    }
                ]
            },
        )

        provider._http_client = AsyncMock()
        provider._http_client.get = AsyncMock(return_value=mock_response)

        voices = await provider.list_voices()
        assert len(voices) == 1
        assert voices[0].language_code == "de-DE"


class TestGoogleCloudTTSProviderSynthesizeREST:
    """Tests for synthesizing audio via REST API (API key path)."""

    @pytest.mark.asyncio
    async def test_synthesize_rest_returns_audio(self):
        from src.providers.google_tts import GoogleCloudTTSProvider

        provider = GoogleCloudTTSProvider(_make_config(api_key="AIza-test-key"))

        fake_audio = b"\xff\xfb\x90\x00" + b"\x00" * 100
        mock_response = httpx.Response(
            200,
            json={"audioContent": base64.b64encode(fake_audio).decode()},
        )

        provider._http_client = AsyncMock()
        provider._http_client.post = AsyncMock(return_value=mock_response)

        result = await provider.synthesize("Hello world", "en-US-Neural2-A", 1.0)
        assert result.audio_bytes == fake_audio
        assert result.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_synthesize_rest_sends_correct_payload(self):
        from src.providers.google_tts import GoogleCloudTTSProvider

        provider = GoogleCloudTTSProvider(_make_config(api_key="AIza-test-key"))

        mock_response = httpx.Response(
            200,
            json={"audioContent": base64.b64encode(b"audio").decode()},
        )

        provider._http_client = AsyncMock()
        provider._http_client.post = AsyncMock(return_value=mock_response)

        await provider.synthesize("Test text", "en-US-Neural2-A", 1.5)

        call_kwargs = provider._http_client.post.call_args
        assert call_kwargs.kwargs["headers"]["X-Goog-Api-Key"] == "AIza-test-key"
        payload = call_kwargs.kwargs["json"]
        assert payload["input"]["text"] == "Test text"
        assert payload["voice"]["name"] == "en-US-Neural2-A"
        assert payload["voice"]["languageCode"] == "en-US"
        assert payload["audioConfig"]["speakingRate"] == 1.5
        assert payload["audioConfig"]["audioEncoding"] == "MP3"

    @pytest.mark.asyncio
    async def test_synthesize_rest_clamps_speed(self):
        from src.providers.google_tts import GoogleCloudTTSProvider

        provider = GoogleCloudTTSProvider(_make_config(api_key="AIza-test-key"))

        mock_response = httpx.Response(
            200,
            json={"audioContent": base64.b64encode(b"audio").decode()},
        )

        provider._http_client = AsyncMock()
        provider._http_client.post = AsyncMock(return_value=mock_response)

        await provider.synthesize("Hello", "en-US-Neural2-A", 10.0)

        call_kwargs = provider._http_client.post.call_args
        payload = call_kwargs.kwargs["json"]
        assert payload["audioConfig"]["speakingRate"] == 4.0

    @pytest.mark.asyncio
    async def test_synthesize_rest_auth_error(self):
        from src.providers.google_tts import GoogleCloudTTSProvider
        from src.errors import ProviderAuthError

        provider = GoogleCloudTTSProvider(_make_config(api_key="bad-key"))

        mock_response = httpx.Response(401, json={"error": {"message": "Unauthorized"}})

        provider._http_client = AsyncMock()
        provider._http_client.post = AsyncMock(return_value=mock_response)

        with pytest.raises(ProviderAuthError):
            await provider.synthesize("Hello", "en-US-Neural2-A", 1.0)

    @pytest.mark.asyncio
    async def test_synthesize_rest_api_error(self):
        from src.providers.google_tts import GoogleCloudTTSProvider
        from src.errors import ProviderAPIError

        provider = GoogleCloudTTSProvider(_make_config(api_key="AIza-test-key"))

        mock_response = httpx.Response(500, json={"error": {"message": "Server error"}})

        provider._http_client = AsyncMock()
        provider._http_client.post = AsyncMock(return_value=mock_response)

        with pytest.raises(ProviderAPIError):
            await provider.synthesize("Hello", "en-US-Neural2-A", 1.0)

    @pytest.mark.asyncio
    async def test_synthesize_rest_extracts_language_code(self):
        from src.providers.google_tts import GoogleCloudTTSProvider

        provider = GoogleCloudTTSProvider(_make_config(api_key="AIza-test-key"))

        mock_response = httpx.Response(
            200,
            json={"audioContent": base64.b64encode(b"audio").decode()},
        )

        provider._http_client = AsyncMock()
        provider._http_client.post = AsyncMock(return_value=mock_response)

        # Voice with standard format
        await provider.synthesize("Hallo", "de-DE-Neural2-B", 1.0)
        payload = provider._http_client.post.call_args.kwargs["json"]
        assert payload["voice"]["languageCode"] == "de-DE"

    @pytest.mark.asyncio
    async def test_synthesize_rest_fallback_language_code(self):
        from src.providers.google_tts import GoogleCloudTTSProvider

        provider = GoogleCloudTTSProvider(_make_config(api_key="AIza-test-key"))

        mock_response = httpx.Response(
            200,
            json={"audioContent": base64.b64encode(b"audio").decode()},
        )

        provider._http_client = AsyncMock()
        provider._http_client.post = AsyncMock(return_value=mock_response)

        # Voice with no dashes -- falls back to en-US
        await provider.synthesize("Hello", "customvoice", 1.0)
        payload = provider._http_client.post.call_args.kwargs["json"]
        assert payload["voice"]["languageCode"] == "en-US"
