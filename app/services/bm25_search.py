"""BM25 Keyword Search Service using BM25Okapi for exact lexical and term matching."""
import logging
import re
from typing import Any, Dict, List, Optional, Set
from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)


def tokenize_text(text: str) -> List[str]:
    """Tokenize text into lowercase alphanumeric terms for BM25 indexing."""
    return re.findall(r"\w+", text.lower())


class BM25SearchService:
    """Maintains an in-memory BM25 index over ingested document chunks."""

    def __init__(self):
        self._chunks: List[Dict[str, Any]] = []
        self._tokenized_corpus: List[List[str]] = []
        self._bm25: Optional[BM25Okapi] = None
        self._chunk_id_to_idx: Dict[str, int] = {}

    def is_empty(self) -> bool:
        """Return True if index contains no chunks."""
        return len(self._chunks) == 0

    def rebuild_index(self, chunks: List[Dict[str, Any]]) -> None:
        """Rebuild entire BM25 index from a full list of chunk dicts."""
        self._chunks = []
        self._tokenized_corpus = []
        self._chunk_id_to_idx = {}

        for i, c in enumerate(chunks):
            self._chunks.append(c)
            self._chunk_id_to_idx[c["chunk_id"]] = i
            self._tokenized_corpus.append(tokenize_text(c["text"]))

        if self._tokenized_corpus:
            self._bm25 = BM25Okapi(self._tokenized_corpus)
            logger.info("BM25 index built with %d chunks.", len(self._chunks))
        else:
            self._bm25 = None

    def add_chunks(self, chunks: List[Dict[str, Any]]) -> None:
        """Add new chunks to the BM25 index."""
        if not chunks:
            return

        for c in chunks:
            # If chunk already in index, update or ignore
            if c["chunk_id"] not in self._chunk_id_to_idx:
                idx = len(self._chunks)
                self._chunks.append(c)
                self._chunk_id_to_idx[c["chunk_id"]] = idx
                self._tokenized_corpus.append(tokenize_text(c["text"]))

        if self._tokenized_corpus:
            self._bm25 = BM25Okapi(self._tokenized_corpus)

    def delete_document_chunks(self, document_id: str) -> None:
        """Remove all chunks associated with a specific document ID and rebuild index."""
        remaining_chunks = [c for c in self._chunks if c.get("document_id") != document_id]
        self.rebuild_index(remaining_chunks)

    def search(
        self,
        query: str,
        top_k: int = 10,
        document_ids: Optional[List[str]] = None,
        file_extensions: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Search BM25 index with optional document and file-extension filters."""
        if not self._bm25 or not self._chunks:
            return []

        query_tokens = tokenize_text(query)
        if not query_tokens:
            return []

        scores = self._bm25.get_scores(query_tokens)
        if len(scores) == 0 or max(scores) <= 0.0:
            return []

        # Filter criteria
        target_doc_ids: Optional[Set[str]] = set(document_ids) if document_ids else None
        target_exts: Optional[Set[str]] = (
            {ext.lower().lstrip(".") for ext in file_extensions} if file_extensions else None
        )

        candidates = []
        for i, score in enumerate(scores):
            if score <= 0.0:
                continue

            chunk = self._chunks[i]
            # Document ID filter
            if target_doc_ids and chunk.get("document_id") not in target_doc_ids:
                continue

            # File extension filter
            if target_exts:
                filename = chunk.get("filename", "").lower()
                ext = filename.rsplit(".", 1)[-1] if "." in filename else ""
                if ext not in target_exts:
                    continue

            candidates.append((score, chunk))

        if not candidates:
            return []

        # Sort descending by score
        candidates.sort(key=lambda x: x[0], reverse=True)
        top_candidates = candidates[:top_k]

        # Min-max normalize scores to [0.0, 1.0]
        max_score = top_candidates[0][0]
        min_score = min(c[0] for c in top_candidates)
        score_range = max_score - min_score if (max_score - min_score) > 1e-6 else 1.0

        results = []
        for score, chunk in top_candidates:
            norm_score = (score - min_score) / score_range if score_range > 0 else 1.0
            results.append(
                {
                    **chunk,
                    "bm25_raw_score": float(score),
                    "relevance_score": float(norm_score),
                }
            )

        return results
