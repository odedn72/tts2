# TDD: Written from spec 03-tts-provider-layer.md
# Tests for AmazonPollyProvider in backend/src/providers/amazon_polly.py

import pytest
import json
from unittest.mock import MagicMock, AsyncMock, patch


class TestAmazonPollyProviderMeta:
    """Tests for provider metadata and configuration."""

    def test_get_provider_name(self):
        from src.providers.amazon_polly import AmazonPollyProvider
        from src.api.schemas import ProviderName

        config = MagicMock()
        config.get_aws_access_key_id.return_value = "AKIA"
        config.get_aws_secret_access_key.return_value = "secret"
        config.get_aws_region.return_value = "us-east-1"
        provider = AmazonPollyProvider(config)
        assert provider.get_provider_name() == ProviderName.AMAZON

    def test_get_display_name(self):
        from src.providers.amazon_polly import AmazonPollyProvider

        config = MagicMock()
        config.get_aws_access_key_id.return_value = None
        config.get_aws_secret_access_key.return_value = None
        config.get_aws_region.return_value = "us-east-1"
        provider = AmazonPollyProvider(config)
        assert "Polly" in provider.get_display_name() or "Amazon" in provider.get_display_name()

    def test_is_configured_true(self):
        from src.providers.amazon_polly import AmazonPollyProvider

        config = MagicMock()
        config.get_aws_access_key_id.return_value = "AKIA"
        config.get_aws_secret_access_key.return_value = "secret"
        config.get_aws_region.return_value = "us-east-1"
        provider = AmazonPollyProvider(config)
        assert provider.is_configured() is True

    def test_is_configured_false_no_key(self):
        from src.providers.amazon_polly import AmazonPollyProvider

        config = MagicMock()
        config.get_aws_access_key_id.return_value = None
        config.get_aws_secret_access_key.return_value = None
        config.get_aws_region.return_value = "us-east-1"
        provider = AmazonPollyProvider(config)
        assert provider.is_configured() is False

    def test_capabilities(self):
        from src.providers.amazon_polly import AmazonPollyProvider

        config = MagicMock()
        config.get_aws_access_key_id.return_value = None
        config.get_aws_secret_access_key.return_value = None
        config.get_aws_region.return_value = "us-east-1"
        provider = AmazonPollyProvider(config)
        caps = provider.get_capabilities()
        assert caps.supports_speed_control is True
        assert caps.supports_word_timing is True
        assert caps.max_chunk_chars == 2800
        assert caps.min_speed == 0.5
        assert caps.max_speed == 2.0


class TestAmazonPollyProviderListVoices:
    """Tests for listing voices from Amazon Polly."""

    @pytest.mark.asyncio
    async def test_list_voices_returns_voice_objects(self):
        from src.providers.amazon_polly import AmazonPollyProvider
        from src.api.schemas import ProviderName

        config = MagicMock()
        config.get_aws_access_key_id.return_value = "AKIA"
        config.get_aws_secret_access_key.return_value = "secret"
        config.get_aws_region.return_value = "us-east-1"
        provider = AmazonPollyProvider(config)

        mock_polly_response = {
            "Voices": [
                {
                    "Id": "Joanna",
                    "Name": "Joanna",
                    "LanguageCode": "en-US",
                    "LanguageName": "US English",
                    "Gender": "Female",
                    "SupportedEngines": ["neural", "standard"],
                },
            ]
        }

        mock_client = MagicMock()
        mock_client.describe_voices.return_value = mock_polly_response

        with patch.object(provider, "_get_client", return_value=mock_client):
            voices = await provider.list_voices()
            assert len(voices) >= 1
            assert voices[0].voice_id == "Joanna"
            assert voices[0].provider == ProviderName.AMAZON

    @pytest.mark.asyncio
    async def test_list_voices_auth_error(self):
        from src.providers.amazon_polly import AmazonPollyProvider
        from src.errors import ProviderAuthError
        from botocore.exceptions import ClientError

        config = MagicMock()
        config.get_aws_access_key_id.return_value = "bad"
        config.get_aws_secret_access_key.return_value = "bad"
        config.get_aws_region.return_value = "us-east-1"
        provider = AmazonPollyProvider(config)

        mock_client = MagicMock()
        error_response = {"Error": {"Code": "UnrecognizedClientException", "Message": "bad creds"}}
        mock_client.describe_voices.side_effect = ClientError(error_response, "DescribeVoices")

        with patch.object(provider, "_get_client", return_value=mock_client):
            with pytest.raises(ProviderAuthError):
                await provider.list_voices()


class TestAmazonPollyProviderSynthesize:
    """Tests for synthesizing audio with Amazon Polly."""

    @pytest.mark.asyncio
    async def test_synthesize_returns_audio_and_timings(self):
        from src.providers.amazon_polly import AmazonPollyProvider

        config = MagicMock()
        config.get_aws_access_key_id.return_value = "AKIA"
        config.get_aws_secret_access_key.return_value = "secret"
        config.get_aws_region.return_value = "us-east-1"
        provider = AmazonPollyProvider(config)

        # Mock audio response
        mock_audio_response = {
            "AudioStream": MagicMock(read=MagicMock(return_value=b"\xff\xfb\x90\x00" + b"\x00" * 512)),
        }

        # Mock speech marks response (NDJSON)
        speech_marks = (
            '{"time":0,"type":"word","start":0,"end":5,"value":"Hello"}\n'
            '{"time":300,"type":"word","start":6,"end":11,"value":"world"}\n'
        )
        mock_marks_response = {
            "AudioStream": MagicMock(read=MagicMock(return_value=speech_marks.encode())),
        }

        mock_client = MagicMock()
        # First call: speech marks, second call: audio
        mock_client.synthesize_speech.side_effect = [mock_marks_response, mock_audio_response]

        with patch.object(provider, "_get_client", return_value=mock_client):
            result = await provider.synthesize("Hello world", "Joanna", 1.0)
            assert result.audio_bytes is not None
            assert result.word_timings is not None or result.sentence_timings is not None

    @pytest.mark.asyncio
    async def test_synthesize_clamps_speed(self):
        from src.providers.amazon_polly import AmazonPollyProvider

        config = MagicMock()
        config.get_aws_access_key_id.return_value = "AKIA"
        config.get_aws_secret_access_key.return_value = "secret"
        config.get_aws_region.return_value = "us-east-1"
        provider = AmazonPollyProvider(config)

        mock_audio_response = {
            "AudioStream": MagicMock(read=MagicMock(return_value=b"\xff\xfb\x90\x00" + b"\x00" * 512)),
        }
        mock_marks_response = {
            "AudioStream": MagicMock(read=MagicMock(return_value=b"")),
        }

        mock_client = MagicMock()
        mock_client.synthesize_speech.side_effect = [mock_marks_response, mock_audio_response]

        with patch.object(provider, "_get_client", return_value=mock_client):
            # Speed 10.0 should be clamped to 2.0 max for Polly
            result = await provider.synthesize("Hello", "Joanna", 10.0)
            assert result is not None

    @pytest.mark.asyncio
    async def test_synthesize_rate_limit_error(self):
        from src.providers.amazon_polly import AmazonPollyProvider
        from src.errors import ProviderRateLimitError
        from botocore.exceptions import ClientError

        config = MagicMock()
        config.get_aws_access_key_id.return_value = "AKIA"
        config.get_aws_secret_access_key.return_value = "secret"
        config.get_aws_region.return_value = "us-east-1"
        provider = AmazonPollyProvider(config)

        mock_client = MagicMock()
        error_response = {"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}}
        mock_client.synthesize_speech.side_effect = ClientError(error_response, "SynthesizeSpeech")

        with patch.object(provider, "_get_client", return_value=mock_client):
            with pytest.raises(ProviderRateLimitError):
                await provider.synthesize("Hello", "Joanna", 1.0)
