# TDD Mode 2: Additional edge case tests discovered during validation review
# These tests cover scenarios not covered by the original TDD test suite.

import pytest


class TestSanitizeProviderError:
    """Tests for the sanitize_provider_error utility in errors.py.

    This function was completely untested in the original suite.
    It protects against API key leakage in error messages.
    """

    def test_sanitize_strips_long_alphanumeric_string(self):
        from src.errors import sanitize_provider_error

        msg = "Auth failed with key AKIAIOSFODNN7EXAMPLEKEY123456"
        result = sanitize_provider_error(msg)
        assert "AKIAIOSFODNN7EXAMPLEKEY123456" not in result
        assert "[REDACTED]" in result

    def test_sanitize_strips_url_with_query_params(self):
        from src.errors import sanitize_provider_error

        msg = "Request to https://api.example.com/v1/tts?key=secret123 failed"
        result = sanitize_provider_error(msg)
        assert "https://api.example.com" not in result
        assert "[URL REDACTED]" in result

    def test_sanitize_preserves_short_strings(self):
        from src.errors import sanitize_provider_error

        msg = "Simple error: bad request"
        result = sanitize_provider_error(msg)
        assert result == msg

    def test_sanitize_handles_empty_string(self):
        from src.errors import sanitize_provider_error

        assert sanitize_provider_error("") == ""

    def test_sanitize_strips_multiple_keys(self):
        from src.errors import sanitize_provider_error

        msg = "Key1: AKIAIOSFODNN7EXAMPLEKEY1 and Key2: sk_live_1234567890abcdefghij"
        result = sanitize_provider_error(msg)
        assert "AKIAIOSFODNN7EXAMPLEKEY1" not in result
        assert "sk_live_1234567890abcdefghij" not in result
        assert result.count("[REDACTED]") >= 2

    def test_sanitize_strips_url_and_key_together(self):
        from src.errors import sanitize_provider_error

        msg = "Call to https://api.elevenlabs.io/v1/tts failed: invalid key sk_1234567890abcdefghijklmno"
        result = sanitize_provider_error(msg)
        assert "https://" not in result
        assert "sk_1234567890" not in result


class TestTextChunkerSingleLongWord:
    """Edge case: a single very long 'word' that exceeds max_chars.

    The chunker should handle this gracefully by splitting at max_chars
    as a last resort.
    """

    def test_single_long_word_is_split_at_max_chars(self):
        from src.processing.chunker import TextChunker

        # A single 'word' of 300 characters with no spaces
        text = "A" * 300
        chunker = TextChunker()
        chunks = chunker.chunk(text, max_chars=100)
        assert len(chunks) >= 3
        for chunk in chunks:
            assert len(chunk.text) <= 100

    def test_single_long_word_offsets_cover_entire_text(self):
        from src.processing.chunker import TextChunker

        text = "B" * 250
        chunker = TextChunker()
        chunks = chunker.chunk(text, max_chars=100)
        # All content should be accounted for
        reconstructed = "".join(c.text for c in chunks)
        assert len(reconstructed) == 250


class TestTextChunkerMaxCharsEdgeBoundaries:
    """Edge cases around max_chars boundary values."""

    def test_max_chars_of_one(self):
        from src.processing.chunker import TextChunker

        chunker = TextChunker()
        chunks = chunker.chunk("AB", max_chars=1)
        assert len(chunks) == 2
        assert chunks[0].text == "A"
        assert chunks[1].text == "B"

    def test_max_chars_equal_to_text_length(self):
        from src.processing.chunker import TextChunker

        text = "Hello world."
        chunker = TextChunker()
        chunks = chunker.chunk(text, max_chars=len(text))
        assert len(chunks) == 1
        assert chunks[0].text == text

    def test_max_chars_one_less_than_text_length(self):
        from src.processing.chunker import TextChunker

        text = "Hello world."
        chunker = TextChunker()
        chunks = chunker.chunk(text, max_chars=len(text) - 1)
        assert len(chunks) >= 2


class TestTimingNormalizerEdgeCases:
    """Edge cases for timing normalization."""

    def test_estimate_sentence_timings_single_word_no_punctuation(self):
        from src.processing.timing import TimingNormalizer

        normalizer = TimingNormalizer()
        result = normalizer.estimate_sentence_timings("Hello", total_duration_ms=500)
        assert len(result) == 1
        assert result[0].start_ms == 0
        assert result[0].end_ms == 500

    def test_estimate_sentence_timings_zero_duration(self):
        from src.processing.timing import TimingNormalizer

        normalizer = TimingNormalizer()
        result = normalizer.estimate_sentence_timings("Hello.", total_duration_ms=0)
        assert len(result) == 1
        assert result[0].start_ms == 0
        assert result[0].end_ms == 0

    def test_split_into_sentences_with_abbreviations(self):
        """Test that abbreviation-like patterns are handled."""
        from src.processing.timing import split_into_sentences

        text = "Dr. Smith went home. He was tired."
        result = split_into_sentences(text)
        # The regex splits on ". " so "Dr. " triggers a split.
        # This is a known limitation but the function should not crash.
        assert len(result) >= 2

    def test_merge_word_timings_with_zero_duration_chunks(self):
        from src.processing.timing import TimingNormalizer
        from src.processing.chunker import TextChunk
        from src.api.schemas import WordTiming

        normalizer = TimingNormalizer()
        chunks = [
            TextChunk(text="A", start_char=0, end_char=1, chunk_index=0, total_chunks=2),
            TextChunk(text="B", start_char=2, end_char=3, chunk_index=1, total_chunks=2),
        ]
        chunk_timings = [
            [WordTiming(word="A", start_ms=0, end_ms=0, start_char=0, end_char=1)],
            [WordTiming(word="B", start_ms=0, end_ms=100, start_char=0, end_char=1)],
        ]
        chunk_durations = [0, 100]

        merged = normalizer.merge_word_timings(chunks, chunk_timings, chunk_durations)
        assert len(merged) == 2
        # Second word should have 0 time offset (first chunk was 0ms)
        assert merged[1].start_ms == 0
        assert merged[1].start_char == 2


class TestAudioStoreEdgeCases:
    """Edge cases for AudioStore file management."""

    def test_save_and_retrieve_empty_bytes(self, tmp_audio_dir):
        from src.processing.audio import AudioStore

        store = AudioStore(tmp_audio_dir)
        path = store.save("empty-job", b"")
        assert path.endswith("empty-job.mp3")
        # Should be retrievable
        retrieved = store.get_path("empty-job")
        assert retrieved == path

    def test_delete_nonexistent_returns_false(self, tmp_audio_dir):
        from src.processing.audio import AudioStore

        store = AudioStore(tmp_audio_dir)
        assert store.delete("nonexistent-job") is False

    def test_get_path_nonexistent_raises_file_not_found(self, tmp_audio_dir):
        from src.processing.audio import AudioStore

        store = AudioStore(tmp_audio_dir)
        with pytest.raises(FileNotFoundError):
            store.get_path("does-not-exist")

    def test_save_overwrites_existing(self, tmp_audio_dir):
        from src.processing.audio import AudioStore

        store = AudioStore(tmp_audio_dir)
        store.save("job-1", b"first")
        store.save("job-1", b"second_content")
        path = store.get_path("job-1")
        with open(path, "rb") as f:
            assert f.read() == b"second_content"


class TestProviderRegistryEdgeCases:
    """Edge cases for the ProviderRegistry."""

    def test_get_configured_providers_when_none_configured(self):
        from src.providers.registry import ProviderRegistry
        from src.api.schemas import ProviderName, ProviderCapabilities
        from unittest.mock import MagicMock

        registry = ProviderRegistry()
        p = MagicMock()
        p.get_provider_name.return_value = ProviderName.GOOGLE
        p.get_display_name.return_value = "Google"
        p.is_configured.return_value = False
        p.get_capabilities.return_value = ProviderCapabilities(
            supports_speed_control=True,
            supports_word_timing=True,
        )
        registry.register(p)
        assert registry.get_configured_providers() == []

    def test_register_all_four_providers(self):
        from src.providers.registry import ProviderRegistry
        from src.api.schemas import ProviderName, ProviderCapabilities
        from unittest.mock import MagicMock

        registry = ProviderRegistry()
        for name in [ProviderName.GOOGLE, ProviderName.AMAZON, ProviderName.ELEVENLABS, ProviderName.OPENAI]:
            p = MagicMock()
            p.get_provider_name.return_value = name
            p.get_display_name.return_value = name.value
            p.is_configured.return_value = True
            p.get_capabilities.return_value = ProviderCapabilities(
                supports_speed_control=True,
                supports_word_timing=False,
            )
            registry.register(p)

        assert len(registry.list_providers()) == 4
        assert len(registry.get_configured_providers()) == 4


class TestRuntimeConfigEdgeCases:
    """Edge cases for RuntimeConfig."""

    def test_is_provider_configured_unknown_provider_returns_false(self, monkeypatch):
        from src.config import RuntimeConfig, Settings

        settings = Settings()
        config = RuntimeConfig(settings)
        # Pass a string that is not a valid ProviderName enum value
        # The checkers dict uses ProviderName enum as keys, so an unknown string won't match
        result = config.is_provider_configured("nonexistent")  # type: ignore
        assert result is False

    def test_override_does_not_affect_other_providers(self, monkeypatch):
        from src.config import RuntimeConfig, Settings
        from src.api.schemas import ProviderName

        settings = Settings()
        config = RuntimeConfig(settings)
        config.set_provider_key(ProviderName.OPENAI, "sk-test")
        # ElevenLabs should still be unconfigured
        assert config.is_provider_configured(ProviderName.ELEVENLABS) is False
        assert config.is_provider_configured(ProviderName.OPENAI) is True


class TestSchemaValidationEdgeCases:
    """Edge cases for Pydantic schema validation."""

    def test_generate_request_text_at_max_length(self):
        from src.api.schemas import GenerateRequest

        text = "A" * 100_000
        req = GenerateRequest(provider="google", voice_id="v1", text=text)
        assert len(req.text) == 100_000

    def test_generate_request_text_exceeds_max_length(self):
        from src.api.schemas import GenerateRequest
        from pydantic import ValidationError

        text = "A" * 100_001
        with pytest.raises(ValidationError):
            GenerateRequest(provider="google", voice_id="v1", text=text)

    def test_generate_request_speed_below_min(self):
        from src.api.schemas import GenerateRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            GenerateRequest(provider="google", voice_id="v1", text="Hello", speed=0.1)

    def test_generate_request_speed_above_max(self):
        from src.api.schemas import GenerateRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            GenerateRequest(provider="google", voice_id="v1", text="Hello", speed=5.0)

    def test_update_settings_request_whitespace_only_key(self):
        from src.api.schemas import UpdateSettingsRequest
        from pydantic import ValidationError

        # A whitespace-only key should still pass min_length=1 since spaces are chars
        # This tests that the schema at least allows it -- the API layer may reject it
        req = UpdateSettingsRequest(provider="openai", api_key=" ")
        assert req.api_key == " "

    def test_provider_name_enum_values(self):
        from src.api.schemas import ProviderName

        assert ProviderName.GOOGLE.value == "google"
        assert ProviderName.AMAZON.value == "amazon"
        assert ProviderName.ELEVENLABS.value == "elevenlabs"
        assert ProviderName.OPENAI.value == "openai"

    def test_invalid_provider_name_raises(self):
        from src.api.schemas import ProviderName

        with pytest.raises(ValueError):
            ProviderName("nonexistent")
