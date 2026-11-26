"""Local text embeddings via fastembed (ONNX). Single entry point for the project.

The model is chosen by EMBEDDING_MODEL in .env. EMBEDDING_DIM must match both the
model's output size and the pgvector column; changing the model means changing both.
"""

from __future__ import annotations

from functools import lru_cache

from fastembed import TextEmbedding

from app.config import get_settings

# Output dimension of paraphrase-multilingual-MiniLM-L12-v2. Keep in sync with the model.
EMBEDDING_DIM = 384


@lru_cache
def _model() -> TextEmbedding:
    """Load the embedding model once (downloaded and cached on first use)."""
    return TextEmbedding(model_name=get_settings().embedding_model)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts into a list of float vectors."""
    return [vector.tolist() for vector in _model().embed(texts)]


def embed_query(text: str) -> list[float]:
    """Embed a single query string into one vector."""
    return embed_texts([text])[0]
