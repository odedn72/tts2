"""
Timing data normalization and sentence splitting utilities.

Merges per-chunk timing data into document-level timing data, and provides
sentence-level timing estimation for providers without native timing support.
"""

import re

from src.api.schemas import SentenceTiming, WordTiming
from src.processing.chunker import TextChunk


def split_into_sentences(text: str) -> list[tuple[str, int, int]]:
    """
    Split text into sentences with character offsets.

    Returns list of (sentence_text, start_char, end_char).

    Uses regex to split on sentence-ending punctuation followed by
    whitespace or end of string.
    """
    pattern = r"(?<=[.!?])\s+"
    parts = re.split(pattern, text)

    result: list[tuple[str, int, int]] = []
    current_offset = 0

    for part in parts:
        if not part:
            continue
        # Find where this part starts in the original text
        start = text.index(part, current_offset)
        end = start + len(part)
        result.append((part, start, end))
        current_offset = end

    return result


class TimingNormalizer:
    """
    Merges per-chunk timing data into document-level timing data.

    When audio chunks are stitched together, the timing offsets for chunk N
    must be shifted by the cumulative duration of chunks 0..N-1.
    Character offsets must be shifted by the chunk's start_char position.
    """

    def merge_word_timings(
        self,
        chunks: list[TextChunk],
        chunk_timings: list[list[WordTiming]],
        chunk_durations_ms: list[int],
        silence_between_ms: int = 0,
    ) -> list[WordTiming]:
        """
        Merge per-chunk word timings into a single document-level list.

        Args:
            chunks: The text chunks (for character offset information).
            chunk_timings: Word timing data for each chunk.
            chunk_durations_ms: Duration of each audio chunk in milliseconds.
            silence_between_ms: Silence inserted between chunks by the stitcher.

        Returns:
            Single list of WordTiming with adjusted offsets.
        """
        merged: list[WordTiming] = []
        cumulative_time_ms = 0

        for i, (chunk, timings, duration) in enumerate(
            zip(chunks, chunk_timings, chunk_durations_ms)
        ):
            for wt in timings:
                merged.append(
                    WordTiming(
                        word=wt.word,
                        start_ms=wt.start_ms + cumulative_time_ms,
                        end_ms=wt.end_ms + cumulative_time_ms,
                        start_char=wt.start_char + chunk.start_char,
                        end_char=wt.end_char + chunk.start_char,
                    )
                )
            cumulative_time_ms += duration
            # Add silence gap between chunks (not after the last one)
            if i < len(chunks) - 1:
                cumulative_time_ms += silence_between_ms

        return merged

    def merge_sentence_timings(
        self,
        chunks: list[TextChunk],
        chunk_timings: list[list[SentenceTiming]],
        chunk_durations_ms: list[int],
        silence_between_ms: int = 0,
    ) -> list[SentenceTiming]:
        """
        Merge per-chunk sentence timings into a single document-level list.

        Same logic as merge_word_timings but for sentence-level data.
        """
        merged: list[SentenceTiming] = []
        cumulative_time_ms = 0

        for i, (chunk, timings, duration) in enumerate(
            zip(chunks, chunk_timings, chunk_durations_ms)
        ):
            for st in timings:
                merged.append(
                    SentenceTiming(
                        sentence=st.sentence,
                        start_ms=st.start_ms + cumulative_time_ms,
                        end_ms=st.end_ms + cumulative_time_ms,
                        start_char=st.start_char + chunk.start_char,
                        end_char=st.end_char + chunk.start_char,
                    )
                )
            cumulative_time_ms += duration
            if i < len(chunks) - 1:
                cumulative_time_ms += silence_between_ms

        return merged

    def estimate_sentence_timings(
        self,
        text: str,
        total_duration_ms: int,
    ) -> list[SentenceTiming]:
        """
        Estimate sentence timing when no timing data is available from the provider.

        Strategy: split text into sentences, distribute total_duration_ms
        proportionally by character count.

        Args:
            text: The full input text.
            total_duration_ms: Total audio duration in milliseconds.

        Returns:
            List of SentenceTiming with estimated start/end times.
        """
        sentences = split_into_sentences(text)

        if not sentences:
            return []

        total_chars = sum(len(s[0]) for s in sentences)
        if total_chars == 0:
            return []

        result: list[SentenceTiming] = []
        current_time_ms = 0

        for i, (sentence_text, start_char, end_char) in enumerate(sentences):
            char_fraction = len(sentence_text) / total_chars
            duration = int(char_fraction * total_duration_ms)

            # Ensure the last sentence ends exactly at total_duration_ms
            if i == len(sentences) - 1:
                end_time = total_duration_ms
            else:
                end_time = current_time_ms + duration

            result.append(
                SentenceTiming(
                    sentence=sentence_text,
                    start_ms=current_time_ms,
                    end_ms=end_time,
                    start_char=start_char,
                    end_char=end_char,
                )
            )
            current_time_ms = end_time

        return result
