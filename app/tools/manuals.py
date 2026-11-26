"""Manual-search tool for the agent (wraps the RAG retriever).

Applies a context-token budget so the manual context handed to the model stays
bounded, and logs how much context actually went in (the context layer).
"""

from __future__ import annotations

import logging
from typing import Any

from app.context import budget_chunks, estimate_tokens
from app.rag.retriever import search

logger = logging.getLogger("foremanai.context")


def search_manuals(query: str, k: int = 5, max_tokens: int = 1200) -> list[dict[str, Any]]:
    """Search the manuals and return the most relevant chunks within a token budget."""
    chunks = search(query, k=k)
    kept = budget_chunks(chunks, max_tokens)

    used_tokens = sum(estimate_tokens(chunk.content) for chunk in kept)
    logger.info(
        "manual context: %d/%d chunks kept, ~%d tokens (budget %d)",
        len(kept),
        len(chunks),
        used_tokens,
        max_tokens,
    )

    return [
        {"citation": chunk.citation, "machine_code": chunk.machine_code, "content": chunk.content}
        for chunk in kept
    ]
