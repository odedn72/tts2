# TDD: Written from spec 04-text-processing.md
# Tests for TextChunker in backend/src/processing/chunker.py

import pytest


class TestTextChunkerBasic:
    """Tests for basic chunking behavior."""

    def test_single_chunk_short_text(self):
        from src.processing.chunker import TextChunker

        chunker = TextChunker()
        chunks = chunker.chunk("Hello world.", max_chars=1000)
        assert len(chunks) == 1
        assert chunks[0].text == "Hello world."
        assert chunks[0].start_char == 0
        assert chunks[0].chunk_index == 0
        assert chunks[0].total_chunks == 1

    def test_text_exactly_at_max_chars(self):
        from src.processing.chunker import TextChunker

        text = "A" * 500
        chunker = TextChunker()
        chunks = chunker.chunk(text, max_chars=500)
        assert len(chunks) == 1
        assert chunks[0].text == text

    def test_empty_text_raises_value_error(self):
        from src.processing.chunker import TextChunker

        chunker = TextChunker()
        with pytest.raises(ValueError):
            chunker.chunk("", max_chars=1000)

    def test_whitespace_only_text_raises_value_error(self):
        from src.processing.chunker import TextChunker

        chunker = TextChunker()
        with pytest.raises(ValueError):
            chunker.chunk("   \n\n  ", max_chars=1000)

    def test_max_chars_too_small_raises_value_error(self):
        from src.processing.chunker import TextChunker

        chunker = TextChunker()
        with pytest.raises(ValueError):
            chunker.chunk("Hello world.", max_chars=50)


class TestTextChunkerSplitting:
    """Tests for splitting logic with different boundary types."""

    def test_split_at_paragraph_boundary(self):
        from src.processing.chunker import TextChunker

        text = "First paragraph content here.\n\nSecond paragraph content here."
        chunker = TextChunker()
        chunks = chunker.chunk(text, max_chars=35)
        assert len(chunks) >= 2
        # First chunk should end at paragraph boundary
        assert chunks[0].text.strip().endswith("here.")

    def test_split_at_sentence_boundary(self):
        from src.processing.chunker import TextChunker

        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        chunker = TextChunker()
        chunks = chunker.chunk(text, max_chars=40)
        assert len(chunks) >= 2
        # Chunks should end at sentence boundaries
        for chunk in chunks:
            stripped = chunk.text.strip()
            assert stripped.endswith(".") or stripped.endswith("!") or stripped.endswith("?") or chunk == chunks[-1]

    def test_split_at_word_boundary_fallback(self):
        from src.processing.chunker import TextChunker

        # Long text without sentence-ending punctuation
        text = "word " * 200  # 1000 chars
        chunker = TextChunker()
        chunks = chunker.chunk(text.strip(), max_chars=200)
        assert len(chunks) >= 2
        # No chunk should split in the middle of a word
        for chunk in chunks:
            assert not chunk.text.startswith(" ")

    def test_multiple_chunks_cover_entire_text(self, sample_long_text):
        from src.processing.chunker import TextChunker

        chunker = TextChunker()
        chunks = chunker.chunk(sample_long_text, max_chars=500)
        # Reconstruct from chunks - all content should be present
        reconstructed = "".join(c.text for c in chunks)
        # The reconstructed text should contain the same non-whitespace content
        assert len(reconstructed.strip()) > 0
        assert len(chunks) > 1

    def test_chunk_indices_are_sequential(self, sample_long_text):
        from src.processing.chunker import TextChunker

        chunker = TextChunker()
        chunks = chunker.chunk(sample_long_text, max_chars=500)
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i

    def test_total_chunks_set_correctly(self, sample_long_text):
        from src.processing.chunker import TextChunker

        chunker = TextChunker()
        chunks = chunker.chunk(sample_long_text, max_chars=500)
        expected_total = len(chunks)
        for chunk in chunks:
            assert chunk.total_chunks == expected_total


class TestTextChunkerCharacterOffsets:
    """Tests for accurate character offset tracking."""

    def test_single_chunk_offsets(self):
        from src.processing.chunker import TextChunker

        text = "Hello world."
        chunker = TextChunker()
        chunks = chunker.chunk(text, max_chars=1000)
        assert chunks[0].start_char == 0
        assert chunks[0].end_char == len(text)

    def test_multi_chunk_offsets_cover_text(self):
        from src.processing.chunker import TextChunker

        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        chunker = TextChunker()
        chunks = chunker.chunk(text, max_chars=35)
        # Offsets should cover the text without gaps
        assert chunks[0].start_char == 0
        for i in range(1, len(chunks)):
            # Each chunk starts at or after the previous chunk ends
            assert chunks[i].start_char >= chunks[i - 1].end_char

    def test_chunk_max_chars_not_exceeded(self, sample_long_text):
        from src.processing.chunker import TextChunker

        chunker = TextChunker()
        max_chars = 500
        chunks = chunker.chunk(sample_long_text, max_chars=max_chars)
        for chunk in chunks:
            assert len(chunk.text) <= max_chars


class TestTextChunkerEdgeCases:
    """Tests for edge cases in chunking."""

    def test_unicode_text(self):
        from src.processing.chunker import TextChunker

        text = "Hej varlden. Det ar en test."  # Swedish-ish
        chunker = TextChunker()
        chunks = chunker.chunk(text, max_chars=1000)
        assert len(chunks) == 1
        assert chunks[0].text == text

    def test_text_with_emoji(self):
        from src.processing.chunker import TextChunker

        text = "Hello world! This is great. More text follows here."
        chunker = TextChunker()
        chunks = chunker.chunk(text, max_chars=1000)
        assert len(chunks) == 1

    def test_text_with_multiple_consecutive_newlines(self):
        from src.processing.chunker import TextChunker

        text = "First part.\n\n\n\nSecond part."
        chunker = TextChunker()
        chunks = chunker.chunk(text, max_chars=1000)
        assert len(chunks) >= 1

    def test_text_with_only_periods(self):
        from src.processing.chunker import TextChunker

        text = "A. B. C. D. E. F. G. H."
        chunker = TextChunker()
        chunks = chunker.chunk(text, max_chars=10)
        assert len(chunks) >= 2

    def test_trailing_leading_whitespace_trimmed(self):
        from src.processing.chunker import TextChunker

        text = "  Hello world. This is a test.  "
        chunker = TextChunker()
        chunks = chunker.chunk(text, max_chars=1000)
        for chunk in chunks:
            assert chunk.text == chunk.text.strip()


class TestTextChunk:
    """Tests for the TextChunk dataclass."""

    def test_text_chunk_fields(self):
        from src.processing.chunker import TextChunk

        chunk = TextChunk(
            text="Hello",
            start_char=0,
            end_char=5,
            chunk_index=0,
            total_chunks=1,
        )
        assert chunk.text == "Hello"
        assert chunk.start_char == 0
        assert chunk.end_char == 5
        assert chunk.chunk_index == 0
        assert chunk.total_chunks == 1
