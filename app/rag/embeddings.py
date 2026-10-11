"""Embedding generation service with CPU-friendly local model and graceful fallback."""
import logging
from typing import List
import numpy as np
from app.config import get_settings

logger = logging.getLogger("querymind.embeddings")
settings = get_settings()

class EmbeddingService:
    """Provides vector embeddings using sentence-transformers or a CPU fallback."""

    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self._model = None
        self._is_fallback = False
        self._init_model()

    def _init_model(self):
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {self.model_name}...")
            # Load in CPU mode
            self._model = SentenceTransformer(self.model_name, device="cpu")
            logger.info("SentenceTransformer model successfully loaded.")
        except Exception as e:
            logger.warning(
                f"Failed to load sentence-transformers model '{self.model_name}' ({e}). "
                "Switching to deterministic hashing/TF-IDF vector fallback."
            )
            self._is_fallback = True

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embeds a list of texts into dense vectors."""
        if not texts:
            return []

        if not self._is_fallback and self._model is not None:
            try:
                embeddings = self._model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
                return embeddings.tolist()
            except Exception as e:
                logger.error(f"Inference error with embedding model: {e}. Falling back.")

        # Fallback deterministic bag-of-words / hashing vector (dim=384)
        vectors = []
        for text in texts:
            vec = np.zeros(384, dtype=np.float32)
            words = text.lower().split()
            for w in words:
                idx = hash(w) % 384
                vec[idx] += 1.0
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec /= norm
            vectors.append(vec.tolist())
        return vectors

    def embed_query(self, query: str) -> List[float]:
        """Embeds a single query string."""
        res = self.embed_texts([query])
        return res[0] if res else [0.0] * 384
