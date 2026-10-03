import hashlib
from typing import List

from django.core.cache import cache

from ai.providers.factory import get_embedding_provider


class EmbeddingService:
    """Thin service over the EmbeddingProvider; queries are cached (embeddings are deterministic)."""

    def __init__(self, provider=None):
        self.provider = provider or get_embedding_provider()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.provider.embed_texts(texts, query=False) if texts else []

    def embed_query(self, text: str) -> List[float]:
        key = "emb:" + hashlib.sha256(f"{self.provider.name}:{text}".encode()).hexdigest()
        hit = cache.get(key)
        if hit is not None:
            return hit
        vec = self.provider.embed_texts([text], query=True)[0]
        cache.set(key, vec, 24 * 3600)
        return vec
