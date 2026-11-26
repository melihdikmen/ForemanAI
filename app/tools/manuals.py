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


def search_manuals(
    query: str,
    machine_code: str | None = None,
    k: int = 5,
    max_tokens: int = 1200,
) -> list[dict[str, Any]]:
    """Search the manuals and return the most relevant chunks within a token budget.

    Pass machine_code (e.g. "PRES-1") to scope the search to one machine's manual,
    which reduces cross-machine noise. Each result includes a relevance score so the
    agent can judge whether to answer or re-search with a refined query.
    """
    chunks = search(query, k=k, machine_code=machine_code)
    kept = budget_chunks(chunks, max_tokens)

    used_tokens = sum(estimate_tokens(chunk.content) for chunk in kept)
    top_score = round(kept[0].score, 3) if kept else 0.0
    logger.info(
        "manual context: %d/%d chunks kept, ~%d tokens, top_score=%s, machine=%s",
        len(kept),
        len(chunks),
        used_tokens,
        top_score,
        machine_code or "all",
    )

    return [
        {
            "citation": chunk.citation,
            "machine_code": chunk.machine_code,
            "score": round(chunk.score, 3),
            "content": chunk.content,
        }
        for chunk in kept
    ]
