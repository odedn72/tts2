# TDD: Written from spec 03-tts-provider-layer.md
# Tests for TTSProvider ABC and SynthesisResult in backend/src/providers/base.py

import pytest


class TestTTSProviderABC:
    """Tests for the TTSProvider abstract base class."""

    def test_cannot_instantiate_directly(self):
        from src.providers.base import TTSProvider

        with pytest.raises(TypeError):
            TTSProvider()

    def test_requires_list_voices(self):
        from src.providers.base import TTSProvider

        assert hasattr(TTSProvider, "list_voices")

    def test_requires_synthesize(self):
        from src.providers.base import TTSProvider

        assert hasattr(TTSProvider, "synthesize")

    def test_requires_get_capabilities(self):
        from src.providers.base import TTSProvider

        assert hasattr(TTSProvider, "get_capabilities")

    def test_requires_is_configured(self):
        from src.providers.base import TTSProvider

        assert hasattr(TTSProvider, "is_configured")

    def test_requires_get_provider_name(self):
        from src.providers.base import TTSProvider

        assert hasattr(TTSProvider, "get_provider_name")

    def test_requires_get_display_name(self):
        from src.providers.base import TTSProvider

        assert hasattr(TTSProvider, "get_display_name")

    def test_incomplete_subclass_cannot_instantiate(self):
        from src.providers.base import TTSProvider

        class PartialProvider(TTSProvider):
            def get_provider_name(self):
                return "test"

        with pytest.raises(TypeError):
            PartialProvider()


class TestSynthesisResult:
    """Tests for the SynthesisResult dataclass."""

    def test_synthesis_result_fields(self):
        from src.providers.base import SynthesisResult

        result = SynthesisResult(
            audio_bytes=b"fake audio",
            word_timings=None,
            sentence_timings=None,
            sample_rate=24000,
            duration_ms=1000,
        )
        assert result.audio_bytes == b"fake audio"
        assert result.word_timings is None
        assert result.sentence_timings is None
        assert result.sample_rate == 24000
        assert result.duration_ms == 1000

    def test_synthesis_result_with_word_timings(self):
        from src.providers.base import SynthesisResult
        from src.api.schemas import WordTiming

        timings = [
            WordTiming(word="Hello", start_ms=0, end_ms=300, start_char=0, end_char=5),
        ]
        result = SynthesisResult(
            audio_bytes=b"audio",
            word_timings=timings,
            sentence_timings=None,
            sample_rate=22050,
            duration_ms=300,
        )
        assert result.word_timings is not None
        assert len(result.word_timings) == 1
