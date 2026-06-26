"""Embedding model wrapper.

Loads a SentenceTransformer once and reuses it. The default model
(all-MiniLM-L6-v2, 384 dims) runs fast on CPU, so no GPU is required.
This matters on macOS, where Docker containers cannot access the Apple
Silicon GPU/Metal anyway.
"""

from functools import lru_cache

from sentence_transformers import SentenceTransformer

from .config import get_settings


@lru_cache
def get_model() -> SentenceTransformer:
    settings = get_settings()
    return SentenceTransformer(settings.embedding_model)


def embed(text: str) -> list[float]:
    """Embed a single string and return a normalized vector."""
    model = get_model()
    vector = model.encode(text, normalize_embeddings=True)
    return vector.tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed many strings at once (used during ingestion)."""
    model = get_model()
    vectors = model.encode(
        texts, normalize_embeddings=True, batch_size=64, show_progress_bar=True
    )
    return [v.tolist() for v in vectors]
