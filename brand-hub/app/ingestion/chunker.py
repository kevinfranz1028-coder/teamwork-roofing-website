"""
Smart text chunking module for Brand Intelligence Content Hub.

Splits text into semantically coherent chunks suitable for embedding
and retrieval, preserving paragraph and sentence boundaries with
configurable overlap for context continuity.
"""

import logging
import re
from typing import Any

import tiktoken

logger = logging.getLogger(__name__)

DEFAULT_MAX_TOKENS = 750
DEFAULT_OVERLAP_TOKENS = 100
DEFAULT_ENCODING = "cl100k_base"


class SemanticChunker:
    """Splits text into overlapping, semantically coherent chunks.

    Uses tiktoken for accurate token counting and prefers splitting at
    paragraph boundaries, then sentence boundaries, then word boundaries.
    Each chunk includes metadata and optional overlap with the previous
    chunk for retrieval context continuity.
    """

    def __init__(self, encoding_name: str = DEFAULT_ENCODING) -> None:
        """Initialize the chunker with a tiktoken encoding.

        Args:
            encoding_name: The tiktoken encoding to use for token counting.
                Defaults to 'cl100k_base' (used by GPT-4, text-embedding-ada-002,
                and similar models).
        """
        try:
            self.encoding = tiktoken.get_encoding(encoding_name)
        except Exception as exc:
            logger.error("Failed to load tiktoken encoding '%s': %s", encoding_name, exc)
            raise

    def chunk(
        self,
        text: str,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        overlap_tokens: int = DEFAULT_OVERLAP_TOKENS,
    ) -> list[dict[str, Any]]:
        """Split text into semantically coherent, overlapping chunks.

        Args:
            text: The input text to chunk.
            max_tokens: Maximum number of tokens per chunk.
            overlap_tokens: Number of tokens to overlap between consecutive
                chunks for context continuity.

        Returns:
            A list of chunk dicts, each containing:
                - text: The chunk text string.
                - token_count: Number of tokens in the chunk.
                - chunk_index: Zero-based chunk index.
                - metadata: Dict with has_overlap (bool) and
                  overlap_tokens (int).

        Raises:
            ValueError: If max_tokens or overlap_tokens are invalid.
        """
        if max_tokens < 1:
            raise ValueError("max_tokens must be at least 1")
        if overlap_tokens < 0:
            raise ValueError("overlap_tokens must be non-negative")
        if overlap_tokens >= max_tokens:
            raise ValueError("overlap_tokens must be less than max_tokens")

        if not text or not text.strip():
            return []

        chunks: list[dict[str, Any]] = []
        remaining = text.strip()
        chunk_index = 0
        previous_chunk_text: str | None = None

        while remaining:
            # Prepend overlap from the previous chunk
            overlap_prefix = ""
            if previous_chunk_text is not None and overlap_tokens > 0:
                overlap_prefix = self._create_overlap(previous_chunk_text, overlap_tokens)

            # Calculate how many tokens we have for new content
            overlap_token_count = self._count_tokens(overlap_prefix)
            available_tokens = max_tokens - overlap_token_count

            if available_tokens < 1:
                # If overlap is too large, just use max_tokens for content
                overlap_prefix = ""
                available_tokens = max_tokens

            # Find how much of the remaining text fits in available_tokens
            chunk_text = self._extract_chunk(remaining, available_tokens)

            if not chunk_text.strip():
                # Safety valve: take at least one character to avoid infinite loop
                if remaining:
                    chunk_text = remaining[:1]
                else:
                    break

            # Build the full chunk with overlap prefix
            full_chunk = (overlap_prefix + " " + chunk_text).strip() if overlap_prefix else chunk_text.strip()

            token_count = self._count_tokens(full_chunk)
            actual_overlap = self._count_tokens(overlap_prefix) if overlap_prefix else 0

            chunks.append({
                "text": full_chunk,
                "token_count": token_count,
                "chunk_index": chunk_index,
                "metadata": {
                    "has_overlap": actual_overlap > 0,
                    "overlap_tokens": actual_overlap,
                },
            })

            # Advance past the text we just consumed (not counting overlap)
            remaining = remaining[len(chunk_text):].strip()
            previous_chunk_text = chunk_text.strip()
            chunk_index += 1

        return chunks

    def _count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string.

        Args:
            text: The text to tokenize and count.

        Returns:
            The number of tokens.
        """
        if not text:
            return 0
        return len(self.encoding.encode(text))

    def _find_break_point(self, text: str, max_pos: int) -> int:
        """Find the best semantic break point at or before max_pos.

        Prefers break points in this order:
          1. Paragraph break (double newline)
          2. Sentence break (period/question mark/exclamation followed by space)
          3. Word break (space)
          4. Hard cut at max_pos

        Args:
            text: The text to search for a break point.
            max_pos: The maximum character position for the break.

        Returns:
            The character index at which to break the text.
        """
        if max_pos >= len(text):
            return len(text)

        search_region = text[:max_pos]

        # 1. Look for paragraph break (double newline)
        para_break = search_region.rfind("\n\n")
        if para_break > max_pos * 0.3:  # Only use if not too far back
            return para_break + 2  # Include the double newline

        # 2. Look for single newline paragraph break
        newline_break = search_region.rfind("\n")
        if newline_break > max_pos * 0.5:
            return newline_break + 1

        # 3. Look for sentence break
        sentence_pattern = re.compile(r'[.!?]\s')
        matches = list(sentence_pattern.finditer(search_region))
        if matches:
            last_match = matches[-1]
            pos = last_match.end()
            if pos > max_pos * 0.3:
                return pos

        # 4. Look for word break (space)
        space_pos = search_region.rfind(" ")
        if space_pos > max_pos * 0.5:
            return space_pos + 1

        # 5. Hard cut at max_pos
        return max_pos

    def _create_overlap(self, previous_chunk: str, overlap_tokens: int) -> str:
        """Extract trailing text from the previous chunk for overlap.

        Takes the last overlap_tokens worth of text from the previous
        chunk, breaking at a semantic boundary when possible.

        Args:
            previous_chunk: The text of the previous chunk.
            overlap_tokens: The target number of overlap tokens.

        Returns:
            A string containing the overlap text from the end of the
            previous chunk.
        """
        if not previous_chunk or overlap_tokens <= 0:
            return ""

        tokens = self.encoding.encode(previous_chunk)
        if len(tokens) <= overlap_tokens:
            return previous_chunk

        # Take the last overlap_tokens tokens
        overlap_tokens_slice = tokens[-overlap_tokens:]
        overlap_text = self.encoding.decode(overlap_tokens_slice).strip()

        # Try to start at a sentence or word boundary
        # Find the first sentence start in the overlap
        sentence_start = re.search(r'(?<=[.!?]\s)', overlap_text)
        if sentence_start and sentence_start.start() < len(overlap_text) * 0.5:
            overlap_text = overlap_text[sentence_start.start():]

        return overlap_text

    def _extract_chunk(self, text: str, max_tokens: int) -> str:
        """Extract a chunk of text that fits within max_tokens.

        Uses binary-search-like approach to find the right amount of
        text, then adjusts to a semantic break point.

        Args:
            text: The remaining text to chunk from.
            max_tokens: Maximum number of tokens for this chunk.

        Returns:
            A substring of text that fits within the token limit and
            ends at a semantic boundary.
        """
        total_tokens = self._count_tokens(text)
        if total_tokens <= max_tokens:
            return text

        # Estimate character position: rough ratio of chars to tokens
        chars_per_token = len(text) / total_tokens if total_tokens > 0 else 4
        estimated_chars = int(max_tokens * chars_per_token)

        # Clamp to text length
        estimated_chars = min(estimated_chars, len(text))

        # Binary-search refinement: ensure we're under max_tokens
        low = 0
        high = estimated_chars
        best = 0

        # Quick check: if our estimate is already under limit, try expanding
        if self._count_tokens(text[:high]) <= max_tokens:
            # Try to expand
            while high < len(text):
                high = min(high + int(chars_per_token * 50), len(text))
                if self._count_tokens(text[:high]) > max_tokens:
                    break
            low = best = estimated_chars
        else:
            # Our estimate was too high, need to shrink
            high = estimated_chars

        # Binary search for the right cutoff
        iterations = 0
        while low <= high and iterations < 30:
            mid = (low + high) // 2
            if self._count_tokens(text[:mid]) <= max_tokens:
                best = mid
                low = mid + 1
            else:
                high = mid - 1
            iterations += 1

        if best == 0:
            # Fallback: at least get one token's worth
            best = max(1, int(chars_per_token))

        # Find a semantic break point near our best position
        break_point = self._find_break_point(text, best)

        # Verify the break point is still within token limit
        if self._count_tokens(text[:break_point]) > max_tokens:
            # Break point pushed us over; fall back to best
            break_point = best

        return text[:break_point]
