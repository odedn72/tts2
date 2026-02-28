# 04 - Text Processing

**Date:** 2026-02-28
**Status:** Draft

## Goal

Define the text chunking strategy and timing data normalization logic. The
chunker splits chapter-length text into provider-appropriate chunks. The timing
normalizer merges per-chunk timing data into a unified document-level timeline.

**MRD traceability:** FR-003 (chapter-length text support), FR-006 (word
timing), FR-007 (sentence fallback), FR-011 (chunking with progress).

## Text Chunker

### Interface

```python
from dataclasses import dataclass


@dataclass
class TextChunk:
    """A chunk of text with its position in the original document."""
    text: str
    start_char: int      # Character offset in original text
    end_char: int        # Character offset in original text
    chunk_index: int     # 0-based chunk number
    total_chunks: int    # Total number of chunks (set after splitting)


class TextChunker:
    """
    Splits text into chunks appropriate for a given provider's limits.

    Splitting rules (in priority order):
    1. Never split in the middle of a word
    2. Prefer splitting at paragraph boundaries (double newline)
    3. Next prefer splitting at sentence boundaries (. ! ? followed by space)
    4. Last resort: split at the nearest word boundary before the limit
    """

    def chunk(self, text: str, max_chars: int) -> list[TextChunk]:
        """
        Split text into chunks of at most max_chars characters each.

        Args:
            text: The full input text.
            max_chars: Maximum characters per chunk (from provider capabilities).

        Returns:
            Ordered list of TextChunk objects covering the entire input text.

        Raises:
            ValueError: If text is empty or max_chars < 100.
        """
        ...
```

### Chunking Algorithm

```
function chunk(text, max_chars):
    chunks = []
    remaining = text
    offset = 0

    while remaining is not empty:
        if len(remaining) <= max_chars:
            # Last chunk
            add chunk(remaining, offset, offset + len(remaining))
            break

        # Find the best split point within max_chars
        candidate = remaining[:max_chars]

        # Try paragraph boundary (last double newline)
        split_pos = candidate.rfind("\n\n")
        if split_pos > max_chars * 0.3:  # Don't split too early
            split_pos += 2  # Include the newlines in the current chunk
        else:
            # Try sentence boundary
            for pattern in [". ", "! ", "? ", ".\n", "!\n", "?\n"]:
                pos = candidate.rfind(pattern)
                if pos > max_chars * 0.3:
                    split_pos = max(split_pos, pos + len(pattern))

        if split_pos <= max_chars * 0.3:
            # Fallback: word boundary
            split_pos = candidate.rfind(" ")
            if split_pos <= 0:
                split_pos = max_chars  # Absolute last resort

        chunk_text = remaining[:split_pos].rstrip()
        add chunk(chunk_text, offset, offset + len(chunk_text))
        remaining = remaining[split_pos:].lstrip()
        offset += split_pos + (original_length - len(remaining_after_lstrip) - len(remaining_before_lstrip))

    set total_chunks on all chunks
    return chunks
```

### Edge Cases

| Case | Handling |
|------|----------|
| Empty text | Raise `ValueError` |
| Text shorter than max_chars | Return single chunk |
| Very long word (> max_chars) | Split at max_chars boundary (should be extremely rare) |
| Text is all whitespace | Raise `ValueError` |
| Multiple consecutive newlines | Collapse to double newline during normalization |
| Trailing/leading whitespace | Trim each chunk |

## Timing Normalizer

### Interface

```python
class TimingNormalizer:
    """
    Merges per-chunk timing data into document-level timing data.

    When audio chunks are stitched together, the timing offsets for chunk N
    must be shifted by the cumulative duration of chunks 0..N-1.
    Character offsets must be shifted by the cumulative character length
    of chunks 0..N-1.
    """

    def merge_word_timings(
        self,
        chunks: list[TextChunk],
        chunk_timings: list[list[WordTiming]],
        chunk_durations_ms: list[int],
    ) -> list[WordTiming]:
        """
        Merge per-chunk word timings into a single document-level list.

        Args:
            chunks: The text chunks (for character offset information).
            chunk_timings: Word timing data for each chunk.
            chunk_durations_ms: Duration of each audio chunk in milliseconds.

        Returns:
            Single list of WordTiming with adjusted offsets.
        """
        ...

    def merge_sentence_timings(
        self,
        chunks: list[TextChunk],
        chunk_timings: list[list[SentenceTiming]],
        chunk_durations_ms: list[int],
    ) -> list[SentenceTiming]:
        """
        Merge per-chunk sentence timings into a single document-level list.

        Same logic as merge_word_timings but for sentence-level data.
        """
        ...

    def estimate_sentence_timings(
        self,
        text: str,
        total_duration_ms: int,
    ) -> list[SentenceTiming]:
        """
        Estimate sentence timing when no timing data is available from the
        provider (e.g., OpenAI TTS).

        Strategy: split text into sentences, distribute total_duration_ms
        proportionally by character count.

        Args:
            text: The full input text.
            total_duration_ms: Total audio duration in milliseconds.

        Returns:
            List of SentenceTiming with estimated start/end times.
        """
        ...
```

### Merge Algorithm

```
function merge_word_timings(chunks, chunk_timings, chunk_durations_ms):
    merged = []
    cumulative_time_ms = 0
    cumulative_chars = 0  # Not needed if chunks carry start_char

    for i, (chunk, timings, duration) in enumerate(zip(chunks, chunk_timings, chunk_durations_ms)):
        for wt in timings:
            merged.append(WordTiming(
                word=wt.word,
                start_ms=wt.start_ms + cumulative_time_ms,
                end_ms=wt.end_ms + cumulative_time_ms,
                start_char=wt.start_char + chunk.start_char,
                end_char=wt.end_char + chunk.start_char,
            ))
        cumulative_time_ms += duration

    return merged
```

### Sentence Splitting (for estimation)

```python
import re

def split_into_sentences(text: str) -> list[tuple[str, int, int]]:
    """
    Split text into sentences with character offsets.

    Returns list of (sentence_text, start_char, end_char).

    Uses regex to split on sentence-ending punctuation followed by
    whitespace or end of string.
    """
    pattern = r'(?<=[.!?])\s+'
    # ... implementation splits while tracking offsets
```

## Dependencies

- `TextChunker` is used by `JobManager` (spec 05) when starting generation
- `TimingNormalizer` is used by `JobManager` after all chunks are synthesized
- Both depend on models from spec 02 (`TextChunk`, `WordTiming`, `SentenceTiming`)

## Error Handling

| Error | When | Handling |
|-------|------|----------|
| `ValueError` | Empty text, text is all whitespace, max_chars too small | Raise immediately; caller should validate before calling |
| Inconsistent timing data | Provider returns fewer timings than expected | Log warning, fall back to sentence-level estimation |

## Notes for Developer

1. The chunker must maintain accurate character offsets. This is critical for
   the highlighting feature. Write thorough tests with texts that include
   multi-byte characters, newlines, and varying whitespace.
2. When stripping whitespace between chunks, be careful to track how many
   characters were consumed so offsets remain accurate.
3. The `estimate_sentence_timings` function is the fallback for providers
   without timing data (currently OpenAI TTS). It should use proportional
   character count, not word count, since speech duration correlates more
   closely with character/syllable count than word count.
4. Test the chunker with:
   - Short text (single chunk)
   - Text exactly at max_chars boundary
   - Text that splits neatly at paragraph boundaries
   - Text with no paragraph breaks (must split at sentences)
   - Text with very long sentences (must split at word boundaries)
   - Unicode text
5. Test the timing normalizer with:
   - Single chunk (no offset adjustment needed)
   - Multiple chunks with known durations
   - Verify that merged timings are monotonically increasing
   - Edge case: chunk with zero words of timing data
