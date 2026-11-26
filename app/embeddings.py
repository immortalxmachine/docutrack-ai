"""
Embedding model wrapper.

Wraps sentence-transformers so the rest of the app never touches it directly.
Vectors are L2-normalised, which means a FAISS inner-product search returns the
cosine similarity — the metric we threshold on for the "I don't know" guard.
The model is loaded lazily and cached, because loading it is the slow part.
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np

from app.config import get_settings


@lru_cache
def _model():
    """Load (once) and cache the sentence-transformers model."""
    from sentence_transformers import SentenceTransformer  # heavy import, kept lazy

    return SentenceTransformer(get_settings().embedding_model)


def embed(texts: list[str], batch_size: int = 32) -> np.ndarray:
    """Embed a list of strings into an (n, dim) float32, L2-normalised matrix.

    Encoding is done in modest batches and the results are accumulated as
    float32, which keeps peak memory low on a large corpus (the real document
    library produces a few thousand chunks, far more than a toy sample).
    """
    model = _model()
    parts: list[np.ndarray] = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]
        vectors = model.encode(
            batch,
            normalize_embeddings=True,  # makes inner product == cosine similarity
            convert_to_numpy=True,
            show_progress_bar=False,
            batch_size=batch_size,
        )
        parts.append(vectors.astype("float32"))
    if not parts:
        return np.empty((0, dimension()), dtype="float32")
    return np.vstack(parts)


def embed_one(text: str) -> np.ndarray:
    """Embed a single string into a (1, dim) matrix (convenience for queries)."""
    return embed([text])


def dimension() -> int:
    """Return the embedding dimension (384 for all-MiniLM-L6-v2)."""
    return _model().get_sentence_embedding_dimension()
