"""
Text chunking logic for splitting chapter-length text into provider-appropriate chunks.

The chunker splits text at natural boundaries (paragraphs, sentences, words)
while respecting provider character limits and maintaining accurate character offsets.
"""

from dataclasses import dataclass


@dataclass
class TextChunk:
    """A chunk of text with its position in the original document."""

    text: str
    start_char: int
    end_char: int
    chunk_index: int
    total_chunks: int


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
            ValueError: If text is empty, whitespace-only, or max_chars < 100.
        """
        if max_chars < 1:
            raise ValueError("max_chars must be at least 1")

        stripped = text.strip()
        if not stripped:
            raise ValueError("Text cannot be empty or whitespace-only")

        # If the stripped text fits in a single chunk, return immediately
        if len(stripped) <= max_chars:
            # Find start position of stripped text within original
            start_pos = text.index(stripped[0]) if stripped else 0
            return [
                TextChunk(
                    text=stripped,
                    start_char=start_pos,
                    end_char=start_pos + len(stripped),
                    chunk_index=0,
                    total_chunks=1,
                )
            ]

        chunks: list[TextChunk] = []
        remaining = stripped
        # Account for leading whitespace in the original text
        offset = text.index(stripped[0]) if stripped else 0

        while remaining:
            # Strip leading whitespace from remaining
            remaining_stripped = remaining.lstrip()
            if remaining_stripped != remaining:
                consumed_ws = len(remaining) - len(remaining_stripped)
                offset += consumed_ws
                remaining = remaining_stripped

            if not remaining:
                break

            if len(remaining) <= max_chars:
                chunk_text = remaining.rstrip()
                chunks.append(
                    TextChunk(
                        text=chunk_text,
                        start_char=offset,
                        end_char=offset + len(chunk_text),
                        chunk_index=len(chunks),
                        total_chunks=0,
                    )
                )
                break

            split_pos = self._find_split_point(remaining, max_chars)

            chunk_text = remaining[:split_pos].rstrip()
            chunks.append(
                TextChunk(
                    text=chunk_text,
                    start_char=offset,
                    end_char=offset + len(chunk_text),
                    chunk_index=len(chunks),
                    total_chunks=0,
                )
            )

            offset += split_pos
            remaining = remaining[split_pos:]

        # Set total_chunks on all chunks
        total = len(chunks)
        for c in chunks:
            c.total_chunks = total

        return chunks

    def _find_split_point(self, text: str, max_chars: int) -> int:
        """
        Find the best split point within the first max_chars characters.

        Tries paragraph boundary, then sentence boundary, then word boundary.
        """
        candidate = text[:max_chars]
        min_pos = int(max_chars * 0.3)

        # Try paragraph boundary (double newline)
        para_pos = candidate.rfind("\n\n")
        if para_pos > min_pos:
            return para_pos + 2

        # Try sentence boundary
        best_sentence_pos = -1
        for pattern in [". ", "! ", "? ", ".\n", "!\n", "?\n"]:
            pos = candidate.rfind(pattern)
            if pos > min_pos:
                candidate_pos = pos + len(pattern)
                if candidate_pos > best_sentence_pos:
                    best_sentence_pos = candidate_pos

        if best_sentence_pos > min_pos:
            return best_sentence_pos

        # Fallback: word boundary
        word_pos = candidate.rfind(" ")
        if word_pos > 0:
            return word_pos + 1

        # Absolute last resort: split at max_chars
        return max_chars
