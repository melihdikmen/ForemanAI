"""Vector similarity search over manual_chunks (the retrieval half of RAG)."""

from __future__ import annotations

from pydantic import BaseModel
from sqlalchemy import select

from app.db import SessionLocal
from app.embedding import embed_query
from app.models import ManualChunk


class RetrievedChunk(BaseModel):
    """A manual chunk returned by search, with its similarity score."""

    machine_code: str
    source: str
    section: str
    content: str
    alarm_codes: str | None
    score: float  # 1 - cosine_distance; higher means more similar

    @property
    def citation(self) -> str:
        """Short source tag the assistant can cite, e.g. '[PRES-3.md · 4.2 ...]'."""
        return f"[{self.source} · {self.section}]"


def search(query: str, k: int = 5) -> list[RetrievedChunk]:
    """Return the top-k manual chunks most similar to the query."""
    query_vector = embed_query(query)
    distance = ManualChunk.embedding.cosine_distance(query_vector)

    with SessionLocal() as session:
        stmt = select(ManualChunk, distance.label("distance")).order_by(distance).limit(k)
        rows = session.execute(stmt).all()

    return [
        RetrievedChunk(
            machine_code=chunk.machine_code,
            source=chunk.source,
            section=chunk.section,
            content=chunk.content,
            alarm_codes=chunk.alarm_codes,
            score=1.0 - float(dist),
        )
        for chunk, dist in rows
    ]
