"""Context layer: decide and measure what enters the model's context window.

The window is a budget. We estimate token cost before sending and keep retrieved
chunks only up to a cap (most-relevant first), so we never overflow or pay for noise.
The exact token count comes back from the API after the call; this is a pre-send estimate.
"""

from __future__ import annotations

from app.rag.retriever import RetrievedChunk

# Rough pre-send estimate. Turkish text is ~1 token per 3.5 characters on average.
CHARS_PER_TOKEN = 3.5


def estimate_tokens(text: str) -> int:
    """Approximate the token count of a string (for budgeting only, not billing)."""
    return int(len(text) / CHARS_PER_TOKEN)


def budget_chunks(chunks: list[RetrievedChunk], max_tokens: int) -> list[RetrievedChunk]:
    """Keep chunks (already sorted most-relevant first) until the token budget runs out."""
    kept: list[RetrievedChunk] = []
    remaining = max_tokens
    for chunk in chunks:
        cost = estimate_tokens(chunk.content)
        if cost > remaining:
            break
        kept.append(chunk)
        remaining -= cost
    return kept
