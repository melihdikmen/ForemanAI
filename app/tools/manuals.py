"""Manual-search tool for the agent (wraps the RAG retriever)."""

from __future__ import annotations

from typing import Any

from app.rag.retriever import search


def search_manuals(query: str, k: int = 5) -> list[dict[str, Any]]:
    """Search the machine manuals and return the most relevant chunks with their sources."""
    return [
        {"citation": chunk.citation, "machine_code": chunk.machine_code, "content": chunk.content}
        for chunk in search(query, k=k)
    ]
