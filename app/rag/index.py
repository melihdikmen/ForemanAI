"""Build the RAG index: chunk the manuals, embed them, store rows in manual_chunks.

Run:  uv run python -m app.rag.index
Safe to re-run: it clears manual_chunks first.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import delete

from app.db import SessionLocal
from app.embedding import embed_texts
from app.models import ManualChunk
from app.rag.chunker import chunk_all

MANUALS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "manuals"


def build_index() -> None:
    """Chunk every manual, embed the chunks, and replace the manual_chunks table."""
    chunks = chunk_all(MANUALS_DIR)
    embeddings = embed_texts([chunk.content for chunk in chunks])

    with SessionLocal() as session:
        session.execute(delete(ManualChunk))
        session.add_all(
            [
                ManualChunk(
                    machine_code=chunk.machine_code,
                    source=chunk.source,
                    section=chunk.section,
                    content=chunk.content,
                    alarm_codes=",".join(chunk.alarm_codes) or None,
                    embedding=embedding,
                )
                for chunk, embedding in zip(chunks, embeddings, strict=True)
            ]
        )
        session.commit()

    print(f"Indexed {len(chunks)} chunks from {MANUALS_DIR}")


if __name__ == "__main__":
    build_index()
