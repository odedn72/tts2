# TDD: Written from spec 04-text-processing.md
# Tests for TimingNormalizer in backend/src/processing/timing.py

import pytest


class TestTimingNormalizerMergeWordTimings:
    """Tests for merging per-chunk word timings into document-level timings."""

    def test_single_chunk_no_offset_adjustment(self):
        from src.processing.timing import TimingNormalizer
        from src.processing.chunker import TextChunk
        from src.api.schemas import WordTiming

        normalizer = TimingNormalizer()
        chunks = [TextChunk(text="Hello world", start_char=0, end_char=11, chunk_index=0, total_chunks=1)]
        chunk_timings = [
            [
                WordTiming(word="Hello", start_ms=0, end_ms=300, start_char=0, end_char=5),
                WordTiming(word="world", start_ms=300, end_ms=600, start_char=6, end_char=11),
            ]
        ]
        chunk_durations = [600]

        merged = normalizer.merge_word_timings(chunks, chunk_timings, chunk_durations)
        assert len(merged) == 2
        assert merged[0].start_ms == 0
        assert merged[0].end_ms == 300
        assert merged[0].start_char == 0
        assert merged[1].start_char == 6

    def test_two_chunks_time_offset_applied(self):
        from src.processing.timing import TimingNormalizer
        from src.processing.chunker import TextChunk
        from src.api.schemas import WordTiming

        normalizer = TimingNormalizer()
        chunks = [
            TextChunk(text="Hello", start_char=0, end_char=5, chunk_index=0, total_chunks=2),
            TextChunk(text="world", start_char=6, end_char=11, chunk_index=1, total_chunks=2),
        ]
        chunk_timings = [
            [WordTiming(word="Hello", start_ms=0, end_ms=300, start_char=0, end_char=5)],
            [WordTiming(word="world", start_ms=0, end_ms=300, start_char=0, end_char=5)],
        ]
        chunk_durations = [300, 300]

        merged = normalizer.merge_word_timings(chunks, chunk_timings, chunk_durations)
        assert len(merged) == 2
        # First chunk word: no offset
        assert merged[0].start_ms == 0
        assert merged[0].end_ms == 300
        assert merged[0].start_char == 0
        # Second chunk word: offset by first chunk duration and start_char
        assert merged[1].start_ms == 300
        assert merged[1].end_ms == 600
        assert merged[1].start_char == 6

    def test_merged_timings_monotonically_increasing(self):
        from src.processing.timing import TimingNormalizer
        from src.processing.chunker import TextChunk
        from src.api.schemas import WordTiming

        normalizer = TimingNormalizer()
        chunks = [
            TextChunk(text="One two", start_char=0, end_char=7, chunk_index=0, total_chunks=3),
            TextChunk(text="three four", start_char=8, end_char=18, chunk_index=1, total_chunks=3),
            TextChunk(text="five six", start_char=19, end_char=27, chunk_index=2, total_chunks=3),
        ]
        chunk_timings = [
            [
                WordTiming(word="One", start_ms=0, end_ms=200, start_char=0, end_char=3),
                WordTiming(word="two", start_ms=200, end_ms=400, start_char=4, end_char=7),
            ],
            [
                WordTiming(word="three", start_ms=0, end_ms=250, start_char=0, end_char=5),
                WordTiming(word="four", start_ms=250, end_ms=500, start_char=6, end_char=10),
            ],
            [
                WordTiming(word="five", start_ms=0, end_ms=200, start_char=0, end_char=4),
                WordTiming(word="six", start_ms=200, end_ms=400, start_char=5, end_char=8),
            ],
        ]
        chunk_durations = [400, 500, 400]

        merged = normalizer.merge_word_timings(chunks, chunk_timings, chunk_durations)
        assert len(merged) == 6
        for i in range(1, len(merged)):
            assert merged[i].start_ms >= merged[i - 1].start_ms

    def test_empty_chunk_timing_handled(self):
        from src.processing.timing import TimingNormalizer
        from src.processing.chunker import TextChunk
        from src.api.schemas import WordTiming

        normalizer = TimingNormalizer()
        chunks = [
            TextChunk(text="Hello", start_char=0, end_char=5, chunk_index=0, total_chunks=2),
            TextChunk(text="world", start_char=6, end_char=11, chunk_index=1, total_chunks=2),
        ]
        chunk_timings = [
            [WordTiming(word="Hello", start_ms=0, end_ms=300, start_char=0, end_char=5)],
            [],  # Empty timing for second chunk
        ]
        chunk_durations = [300, 300]

        merged = normalizer.merge_word_timings(chunks, chunk_timings, chunk_durations)
        assert len(merged) == 1


class TestTimingNormalizerMergeSentenceTimings:
    """Tests for merging per-chunk sentence timings."""

    def test_single_chunk_sentence_timing(self):
        from src.processing.timing import TimingNormalizer
        from src.processing.chunker import TextChunk
        from src.api.schemas import SentenceTiming

        normalizer = TimingNormalizer()
        chunks = [TextChunk(text="Hello world.", start_char=0, end_char=12, chunk_index=0, total_chunks=1)]
        chunk_timings = [
            [SentenceTiming(sentence="Hello world.", start_ms=0, end_ms=600, start_char=0, end_char=12)]
        ]
        chunk_durations = [600]

        merged = normalizer.merge_sentence_timings(chunks, chunk_timings, chunk_durations)
        assert len(merged) == 1
        assert merged[0].start_ms == 0

    def test_two_chunks_sentence_timing_offset(self):
        from src.processing.timing import TimingNormalizer
        from src.processing.chunker import TextChunk
        from src.api.schemas import SentenceTiming

        normalizer = TimingNormalizer()
        chunks = [
            TextChunk(text="First sentence.", start_char=0, end_char=15, chunk_index=0, total_chunks=2),
            TextChunk(text="Second sentence.", start_char=16, end_char=32, chunk_index=1, total_chunks=2),
        ]
        chunk_timings = [
            [SentenceTiming(sentence="First sentence.", start_ms=0, end_ms=500, start_char=0, end_char=15)],
            [SentenceTiming(sentence="Second sentence.", start_ms=0, end_ms=600, start_char=0, end_char=16)],
        ]
        chunk_durations = [500, 600]

        merged = normalizer.merge_sentence_timings(chunks, chunk_timings, chunk_durations)
        assert len(merged) == 2
        assert merged[1].start_ms == 500
        assert merged[1].end_ms == 1100
        assert merged[1].start_char == 16


class TestTimingNormalizerEstimateSentenceTimings:
    """Tests for estimating sentence timings when provider has none."""

    def test_estimate_single_sentence(self):
        from src.processing.timing import TimingNormalizer

        normalizer = TimingNormalizer()
        text = "Hello world."
        result = normalizer.estimate_sentence_timings(text, total_duration_ms=600)
        assert len(result) == 1
        assert result[0].start_ms == 0
        assert result[0].end_ms == 600
        assert result[0].start_char == 0

    def test_estimate_multiple_sentences(self):
        from src.processing.timing import TimingNormalizer

        normalizer = TimingNormalizer()
        text = "Short. A much longer sentence here."
        result = normalizer.estimate_sentence_timings(text, total_duration_ms=1000)
        assert len(result) == 2
        # Proportional distribution: first sentence is shorter
        assert result[0].end_ms < result[1].end_ms - result[1].start_ms + result[0].start_ms
        # Times should be contiguous
        assert result[1].start_ms == result[0].end_ms

    def test_estimate_preserves_character_offsets(self):
        from src.processing.timing import TimingNormalizer

        normalizer = TimingNormalizer()
        text = "First. Second."
        result = normalizer.estimate_sentence_timings(text, total_duration_ms=1000)
        assert result[0].start_char == 0
        # Second sentence starts after "First. "
        assert result[1].start_char > 0
        assert result[1].end_char == len(text)

    def test_estimate_total_duration_matches(self):
        from src.processing.timing import TimingNormalizer

        normalizer = TimingNormalizer()
        text = "One sentence. Two sentence. Three sentence."
        result = normalizer.estimate_sentence_timings(text, total_duration_ms=3000)
        assert result[-1].end_ms == 3000
        assert result[0].start_ms == 0


class TestSentenceSplitting:
    """Tests for the sentence splitting utility function."""

    def test_split_simple_sentences(self):
        from src.processing.timing import split_into_sentences

        result = split_into_sentences("Hello world. This is a test.")
        assert len(result) == 2
        assert result[0][0].strip() == "Hello world."
        assert result[1][0].strip() == "This is a test."

    def test_split_exclamation_and_question(self):
        from src.processing.timing import split_into_sentences

        result = split_into_sentences("Really? Yes! Okay.")
        assert len(result) == 3

    def test_split_preserves_offsets(self):
        from src.processing.timing import split_into_sentences

        text = "First. Second."
        result = split_into_sentences(text)
        for sentence_text, start, end in result:
            assert text[start:end].strip() == sentence_text.strip()

    def test_split_single_sentence(self):
        from src.processing.timing import split_into_sentences

        result = split_into_sentences("Just one sentence.")
        assert len(result) == 1

    def test_split_no_trailing_punctuation(self):
        from src.processing.timing import split_into_sentences

        result = split_into_sentences("This has no ending punctuation")
        assert len(result) == 1
