from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Any, List, Optional

if TYPE_CHECKING:
    from app.services.retriever import RetrievedChunk

logger = logging.getLogger(__name__)


class CrossEncoderReranker:
    """Reranks retrieved candidate chunks using a deep cross-encoder model."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2", device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self._model = None
        self._load_failed = False

    def _get_model(self):
        """Lazy load CrossEncoder model."""
        if self._model is None and not self._load_failed:
            try:
                from sentence_transformers import CrossEncoder

                logger.info("Loading CrossEncoder model '%s' on %s...", self.model_name, self.device)
                self._model = CrossEncoder(self.model_name, device=self.device)
                logger.info("CrossEncoder model loaded successfully.")
            except Exception as e:
                logger.warning("Could not load CrossEncoder model '%s': %s. Falling back to heuristic reranker.", self.model_name, e)
                self._load_failed = True
        return self._model

    def rerank(
        self,
        query: str,
        chunks: List[RetrievedChunk],
        top_k: int = 5,
    ) -> List[RetrievedChunk]:
        """Rerank candidates based on deep cross-encoder relevance scores."""
        if not chunks:
            return []
        if len(chunks) <= 1:
            return chunks[:top_k]

        model = self._get_model()
        if model is not None:
            try:
                pairs = [[query, c.text] for c in chunks]
                scores = model.predict(pairs)

                # Min-max normalize scores to [0.0, 1.0]
                min_s = float(min(scores))
                max_s = float(max(scores))
                diff = max_s - min_s if (max_s - min_s) > 1e-6 else 1.0

                reranked = []
                for chunk, raw_score in zip(chunks, scores):
                    norm_score = round(float((raw_score - min_s) / diff), 4) if diff > 0 else 1.0
                    reranked.append(
                        chunk.__class__(
                            chunk_id=chunk.chunk_id,
                            document_id=chunk.document_id,
                            chunk_index=chunk.chunk_index,
                            filename=chunk.filename,
                            page_number=chunk.page_number,
                            text=chunk.text,
                            relevance_score=norm_score,
                            distance=chunk.distance,
                        )
                    )

                reranked.sort(key=lambda c: c.relevance_score, reverse=True)
                return reranked[:top_k]
            except Exception as e:
                logger.warning("CrossEncoder prediction error: %s. Returning un-reranked chunks.", e)

        # Fallback: maintain original ranking trimmed to top_k
        return chunks[:top_k]
