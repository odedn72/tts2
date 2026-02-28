# TDD: Written from spec 02-data-models.md
# Tests for Pydantic data models in backend/src/api/schemas.py

import pytest


class TestProviderName:
    """Tests for the ProviderName enum."""

    def test_provider_name_values(self):
        from src.api.schemas import ProviderName

        assert ProviderName.GOOGLE == "google"
        assert ProviderName.AMAZON == "amazon"
        assert ProviderName.ELEVENLABS == "elevenlabs"
        assert ProviderName.OPENAI == "openai"

    def test_provider_name_from_string(self):
        from src.api.schemas import ProviderName

        assert ProviderName("google") == ProviderName.GOOGLE
        assert ProviderName("amazon") == ProviderName.AMAZON

    def test_provider_name_invalid_raises(self):
        from src.api.schemas import ProviderName

        with pytest.raises(ValueError):
            ProviderName("invalid_provider")

    def test_provider_name_is_string(self):
        from src.api.schemas import ProviderName

        assert isinstance(ProviderName.GOOGLE, str)


class TestProviderCapabilities:
    """Tests for the ProviderCapabilities model."""

    def test_provider_capabilities_defaults(self):
        from src.api.schemas import ProviderCapabilities

        caps = ProviderCapabilities(
            supports_speed_control=True,
            supports_word_timing=True,
        )
        assert caps.min_speed == 0.25
        assert caps.max_speed == 4.0
        assert caps.default_speed == 1.0
        assert caps.max_chunk_chars == 5000

    def test_provider_capabilities_custom(self):
        from src.api.schemas import ProviderCapabilities

        caps = ProviderCapabilities(
            supports_speed_control=False,
            supports_word_timing=False,
            min_speed=0.5,
            max_speed=2.0,
            default_speed=1.0,
            max_chunk_chars=2800,
        )
        assert caps.supports_speed_control is False
        assert caps.supports_word_timing is False
        assert caps.max_chunk_chars == 2800

    def test_provider_capabilities_serialization(self):
        from src.api.schemas import ProviderCapabilities

        caps = ProviderCapabilities(
            supports_speed_control=True,
            supports_word_timing=True,
        )
        data = caps.model_dump(mode="json")
        assert data["supports_speed_control"] is True
        assert data["min_speed"] == 0.25


class TestProviderInfo:
    """Tests for the ProviderInfo model."""

    def test_provider_info_creation(self):
        from src.api.schemas import ProviderInfo, ProviderName, ProviderCapabilities

        info = ProviderInfo(
            name=ProviderName.GOOGLE,
            display_name="Google Cloud TTS",
            capabilities=ProviderCapabilities(
                supports_speed_control=True,
                supports_word_timing=True,
            ),
            is_configured=True,
        )
        assert info.name == ProviderName.GOOGLE
        assert info.display_name == "Google Cloud TTS"
        assert info.is_configured is True

    def test_provider_info_json_serialization(self):
        from src.api.schemas import ProviderInfo, ProviderName, ProviderCapabilities

        info = ProviderInfo(
            name=ProviderName.OPENAI,
            display_name="OpenAI TTS",
            capabilities=ProviderCapabilities(
                supports_speed_control=True,
                supports_word_timing=False,
            ),
            is_configured=False,
        )
        data = info.model_dump(mode="json")
        assert data["name"] == "openai"
        assert data["is_configured"] is False
        assert data["capabilities"]["supports_word_timing"] is False


class TestVoice:
    """Tests for the Voice model."""

    def test_voice_creation(self):
        from src.api.schemas import Voice, ProviderName

        voice = Voice(
            voice_id="en-US-Neural2-A",
            name="Neural2-A",
            language_code="en-US",
            language_name="English (US)",
            gender="FEMALE",
            provider=ProviderName.GOOGLE,
        )
        assert voice.voice_id == "en-US-Neural2-A"
        assert voice.gender == "FEMALE"

    def test_voice_gender_optional(self):
        from src.api.schemas import Voice, ProviderName

        voice = Voice(
            voice_id="alloy",
            name="Alloy",
            language_code="en-US",
            language_name="English (US)",
            gender=None,
            provider=ProviderName.OPENAI,
        )
        assert voice.gender is None

    def test_voice_serialization(self):
        from src.api.schemas import Voice, ProviderName

        voice = Voice(
            voice_id="Joanna",
            name="Joanna",
            language_code="en-US",
            language_name="English (US)",
            gender="FEMALE",
            provider=ProviderName.AMAZON,
        )
        data = voice.model_dump(mode="json")
        assert data["voice_id"] == "Joanna"
        assert data["provider"] == "amazon"


class TestVoiceListResponse:
    """Tests for VoiceListResponse."""

    def test_voice_list_response(self):
        from src.api.schemas import VoiceListResponse, Voice, ProviderName

        resp = VoiceListResponse(
            provider=ProviderName.GOOGLE,
            voices=[
                Voice(
                    voice_id="en-US-Neural2-A",
                    name="Neural2-A",
                    language_code="en-US",
                    language_name="English (US)",
                    gender="FEMALE",
                    provider=ProviderName.GOOGLE,
                )
            ],
        )
        assert resp.provider == ProviderName.GOOGLE
        assert len(resp.voices) == 1

    def test_voice_list_response_empty_voices(self):
        from src.api.schemas import VoiceListResponse, ProviderName

        resp = VoiceListResponse(provider=ProviderName.OPENAI, voices=[])
        assert resp.voices == []


class TestGenerationStatus:
    """Tests for GenerationStatus enum."""

    def test_generation_status_values(self):
        from src.api.schemas import GenerationStatus

        assert GenerationStatus.PENDING == "pending"
        assert GenerationStatus.IN_PROGRESS == "in_progress"
        assert GenerationStatus.COMPLETED == "completed"
        assert GenerationStatus.FAILED == "failed"


class TestGenerateRequest:
    """Tests for GenerateRequest validation."""

    def test_valid_generate_request(self):
        from src.api.schemas import GenerateRequest, ProviderName

        req = GenerateRequest(
            provider=ProviderName.GOOGLE,
            voice_id="en-US-Neural2-A",
            text="Hello world",
            speed=1.0,
        )
        assert req.text == "Hello world"
        assert req.speed == 1.0

    def test_generate_request_default_speed(self):
        from src.api.schemas import GenerateRequest, ProviderName

        req = GenerateRequest(
            provider=ProviderName.GOOGLE,
            voice_id="test",
            text="Hello",
        )
        assert req.speed == 1.0

    def test_generate_request_text_too_short(self):
        from src.api.schemas import GenerateRequest, ProviderName
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            GenerateRequest(
                provider=ProviderName.GOOGLE,
                voice_id="test",
                text="",
            )

    def test_generate_request_text_too_long(self):
        from src.api.schemas import GenerateRequest, ProviderName
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            GenerateRequest(
                provider=ProviderName.GOOGLE,
                voice_id="test",
                text="x" * 100_001,
            )

    def test_generate_request_speed_below_min(self):
        from src.api.schemas import GenerateRequest, ProviderName
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            GenerateRequest(
                provider=ProviderName.GOOGLE,
                voice_id="test",
                text="Hello",
                speed=0.1,
            )

    def test_generate_request_speed_above_max(self):
        from src.api.schemas import GenerateRequest, ProviderName
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            GenerateRequest(
                provider=ProviderName.GOOGLE,
                voice_id="test",
                text="Hello",
                speed=5.0,
            )

    def test_generate_request_invalid_provider(self):
        from src.api.schemas import GenerateRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            GenerateRequest(
                provider="invalid",
                voice_id="test",
                text="Hello",
            )

    def test_generate_request_text_at_max_boundary(self):
        from src.api.schemas import GenerateRequest, ProviderName

        req = GenerateRequest(
            provider=ProviderName.GOOGLE,
            voice_id="test",
            text="x" * 100_000,
        )
        assert len(req.text) == 100_000

    def test_generate_request_speed_at_boundaries(self):
        from src.api.schemas import GenerateRequest, ProviderName

        req_min = GenerateRequest(
            provider=ProviderName.GOOGLE,
            voice_id="test",
            text="Hello",
            speed=0.25,
        )
        assert req_min.speed == 0.25

        req_max = GenerateRequest(
            provider=ProviderName.GOOGLE,
            voice_id="test",
            text="Hello",
            speed=4.0,
        )
        assert req_max.speed == 4.0


class TestGenerateResponse:
    """Tests for GenerateResponse."""

    def test_generate_response(self):
        from src.api.schemas import GenerateResponse, GenerationStatus

        resp = GenerateResponse(job_id="abc-123", status=GenerationStatus.PENDING)
        data = resp.model_dump(mode="json")
        assert data["job_id"] == "abc-123"
        assert data["status"] == "pending"


class TestJobStatusResponse:
    """Tests for JobStatusResponse."""

    def test_job_status_in_progress(self):
        from src.api.schemas import JobStatusResponse, GenerationStatus

        resp = JobStatusResponse(
            job_id="abc-123",
            status=GenerationStatus.IN_PROGRESS,
            progress=0.6,
            total_chunks=5,
            completed_chunks=3,
            error_message=None,
        )
        assert resp.progress == 0.6
        assert resp.error_message is None

    def test_job_status_failed_with_message(self):
        from src.api.schemas import JobStatusResponse, GenerationStatus

        resp = JobStatusResponse(
            job_id="abc-123",
            status=GenerationStatus.FAILED,
            progress=0.4,
            total_chunks=5,
            completed_chunks=2,
            error_message="Rate limit exceeded",
        )
        assert resp.error_message == "Rate limit exceeded"

    def test_job_status_completed(self):
        from src.api.schemas import JobStatusResponse, GenerationStatus

        resp = JobStatusResponse(
            job_id="abc-123",
            status=GenerationStatus.COMPLETED,
            progress=1.0,
            total_chunks=5,
            completed_chunks=5,
        )
        assert resp.progress == 1.0


class TestTimingModels:
    """Tests for WordTiming, SentenceTiming, and TimingData."""

    def test_word_timing(self):
        from src.api.schemas import WordTiming

        wt = WordTiming(
            word="Hello",
            start_ms=0,
            end_ms=300,
            start_char=0,
            end_char=5,
        )
        assert wt.word == "Hello"
        assert wt.start_ms == 0
        assert wt.end_ms == 300

    def test_sentence_timing(self):
        from src.api.schemas import SentenceTiming

        st = SentenceTiming(
            sentence="Hello world.",
            start_ms=0,
            end_ms=600,
            start_char=0,
            end_char=12,
        )
        assert st.sentence == "Hello world."

    def test_timing_data_word_type(self):
        from src.api.schemas import TimingData, WordTiming

        td = TimingData(
            timing_type="word",
            words=[
                WordTiming(word="Hi", start_ms=0, end_ms=200, start_char=0, end_char=2),
            ],
            sentences=None,
        )
        assert td.timing_type == "word"
        assert td.words is not None
        assert td.sentences is None

    def test_timing_data_sentence_type(self):
        from src.api.schemas import TimingData, SentenceTiming

        td = TimingData(
            timing_type="sentence",
            words=None,
            sentences=[
                SentenceTiming(
                    sentence="Hello.", start_ms=0, end_ms=300, start_char=0, end_char=6
                ),
            ],
        )
        assert td.timing_type == "sentence"
        assert td.sentences is not None
        assert td.words is None

    def test_timing_data_serialization(self):
        from src.api.schemas import TimingData, WordTiming

        td = TimingData(
            timing_type="word",
            words=[
                WordTiming(word="Hi", start_ms=0, end_ms=200, start_char=0, end_char=2),
            ],
            sentences=None,
        )
        data = td.model_dump(mode="json")
        assert data["timing_type"] == "word"
        assert len(data["words"]) == 1
        assert data["sentences"] is None


class TestAudioMetadataResponse:
    """Tests for AudioMetadataResponse."""

    def test_audio_metadata_response(self):
        from src.api.schemas import AudioMetadataResponse, TimingData, WordTiming

        resp = AudioMetadataResponse(
            job_id="abc-123",
            duration_ms=5000,
            format="mp3",
            size_bytes=50000,
            timing=TimingData(
                timing_type="word",
                words=[
                    WordTiming(word="Hi", start_ms=0, end_ms=200, start_char=0, end_char=2),
                ],
                sentences=None,
            ),
        )
        assert resp.duration_ms == 5000
        assert resp.format == "mp3"


class TestSettingsModels:
    """Tests for settings-related models."""

    def test_provider_key_status(self):
        from src.api.schemas import ProviderKeyStatus, ProviderName

        status = ProviderKeyStatus(
            provider=ProviderName.GOOGLE,
            is_configured=True,
        )
        assert status.is_configured is True

    def test_settings_response(self):
        from src.api.schemas import SettingsResponse, ProviderKeyStatus, ProviderName

        resp = SettingsResponse(
            providers=[
                ProviderKeyStatus(provider=ProviderName.GOOGLE, is_configured=True),
                ProviderKeyStatus(provider=ProviderName.OPENAI, is_configured=False),
            ]
        )
        assert len(resp.providers) == 2

    def test_update_settings_request_valid(self):
        from src.api.schemas import UpdateSettingsRequest, ProviderName

        req = UpdateSettingsRequest(
            provider=ProviderName.OPENAI,
            api_key="sk-test123",
        )
        assert req.api_key == "sk-test123"

    def test_update_settings_request_empty_key_rejected(self):
        from src.api.schemas import UpdateSettingsRequest, ProviderName
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            UpdateSettingsRequest(
                provider=ProviderName.OPENAI,
                api_key="",
            )

    def test_settings_response_never_contains_keys(self):
        """Verify the SettingsResponse model has no field for actual API keys."""
        from src.api.schemas import SettingsResponse

        fields = SettingsResponse.model_fields
        for field_name in fields:
            assert "key" not in field_name.lower() or field_name == "is_configured"
        # Also check ProviderKeyStatus
        from src.api.schemas import ProviderKeyStatus

        pks_fields = ProviderKeyStatus.model_fields
        field_names = list(pks_fields.keys())
        assert "api_key" not in field_names
