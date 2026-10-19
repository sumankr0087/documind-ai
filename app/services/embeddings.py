"""Embedding service using Sentence Transformers with caching and batch processing."""
import logging
from typing import List, Optional
import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Wraps SentenceTransformer for generating vector representations of text."""

    _instance: Optional["EmbeddingService"] = None
    _model = None

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self._load_model()

    def _load_model(self) -> None:
        """Lazily load the SentenceTransformer model."""
        if EmbeddingService._model is None:
            logger.info("Loading SentenceTransformer model: %s on %s", self.model_name, self.device)
            try:
                from sentence_transformers import SentenceTransformer
                try:
                    EmbeddingService._model = SentenceTransformer(
                        self.model_name, device=self.device, local_files_only=True
                    )
                except Exception:
                    EmbeddingService._model = SentenceTransformer(self.model_name, device=self.device)
            except Exception as e:
                logger.error("Failed to load SentenceTransformer '%s': %s", self.model_name, e)
                raise RuntimeError(f"Embedding model initialization failed: {e}") from e

    @property
    def model(self):
        if EmbeddingService._model is None:
            self._load_model()
        return EmbeddingService._model

    def embed_query(self, query: str) -> List[float]:
        """Generate embedding vector for a single query text."""
        cleaned_query = query.strip()
        if not cleaned_query:
            raise ValueError("Query string cannot be empty")

        embedding = self.model.encode(cleaned_query, convert_to_numpy=True, normalize_embeddings=True)
        return embedding.tolist()

    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """Generate normalized embedding vectors for a batch of documents."""
        if not documents:
            return []

        cleaned_docs = [d.strip() if d.strip() else " " for d in documents]
        embeddings = self.model.encode(
            cleaned_docs,
            batch_size=32,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embeddings.tolist()

    @property
    def dimension(self) -> int:
        """Return the dimensionality of the generated embeddings."""
        return self.model.get_sentence_embedding_dimension()
