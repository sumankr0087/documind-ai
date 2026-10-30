"""Retriever service supporting Dense, Semantic MMR, BM25 Hybrid Search, and Cross-Encoder Reranking."""
import logging
import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set
import numpy as np

from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStoreService
from app.services.bm25_search import BM25SearchService
from app.services.reranker import CrossEncoderReranker

logger = logging.getLogger(__name__)


class DocumentNotFoundError(Exception):
    """Raised when a specified document_id filter does not exist."""
    pass


@dataclass
class RetrievedChunk:
    """Represents a retrieved document chunk with relevance metrics."""
    chunk_id: str
    document_id: str
    chunk_index: int
    filename: str
    page_number: Optional[int]
    text: str
    relevance_score: float
    distance: float


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    dot = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def maximal_marginal_relevance(
    query_embedding: List[float],
    candidate_embeddings: List[List[float]],
    candidate_chunks: List[RetrievedChunk],
    k: int = 5,
    lambda_mult: float = 0.7,
) -> List[RetrievedChunk]:
    """Calculate Maximal Marginal Relevance (MMR) to balance query relevance and content diversity."""
    if not candidate_chunks or not candidate_embeddings:
        return []
    if len(candidate_chunks) <= k:
        return candidate_chunks
    if len(candidate_chunks) != len(candidate_embeddings):
        # Truncate or fallback safely
        min_len = min(len(candidate_chunks), len(candidate_embeddings))
        candidate_chunks = candidate_chunks[:min_len]
        candidate_embeddings = candidate_embeddings[:min_len]

    selected_indices: List[int] = []
    unselected_indices: List[int] = list(range(len(candidate_chunks)))

    # Compute similarity of each candidate to query
    sim_to_query = [
        cosine_similarity(query_embedding, emb) for emb in candidate_embeddings
    ]

    # First chunk is the one with highest similarity to query
    first_idx = int(np.argmax(sim_to_query))
    selected_indices.append(first_idx)
    unselected_indices.remove(first_idx)

    # Greedily pick remaining (k - 1) chunks
    while len(selected_indices) < k and unselected_indices:
        best_score = -float("inf")
        best_idx = unselected_indices[0]

        for u_idx in unselected_indices:
            # Relevance to query
            rel_score = sim_to_query[u_idx]

            # Maximum similarity to already selected chunks
            max_sim_to_selected = max(
                cosine_similarity(candidate_embeddings[u_idx], candidate_embeddings[s_idx])
                for s_idx in selected_indices
            )

            # MMR formula
            mmr_score = lambda_mult * rel_score - (1.0 - lambda_mult) * max_sim_to_selected
            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = u_idx

        selected_indices.append(best_idx)
        unselected_indices.remove(best_idx)

    return [candidate_chunks[i] for i in selected_indices]


class RetrieverService:
    """Orchestrates query embedding, vector similarity search, BM25 hybrid search, MMR, and reranking."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStoreService,
        bm25_service: Optional[BM25SearchService] = None,
        reranker: Optional[CrossEncoderReranker] = None,
    ):
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.bm25_service = bm25_service
        self.reranker = reranker

    def retrieve(
        self,
        question: str,
        top_k: int = 5,
        document_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
        file_extensions: Optional[List[str]] = None,
        enable_mmr: bool = False,
        mmr_lambda: float = 0.7,
        enable_hybrid: bool = False,
        hybrid_dense_weight: float = 0.6,
        hybrid_bm25_weight: float = 0.4,
        enable_reranking: bool = False,
    ) -> List[RetrievedChunk]:
        """Retrieve relevant chunks using standard Dense, Semantic MMR, Hybrid (Dense+BM25), or Reranked search."""
        cleaned_question = question.strip()
        if not cleaned_question:
            return []

        # 1. Resolve document filtering
        target_doc_ids: Optional[List[str]] = None
        if document_ids:
            target_doc_ids = [d for d in document_ids if d]
        elif document_id:
            target_doc_ids = [document_id]

        if target_doc_ids:
            # Verify documents exist
            for d_id in target_doc_ids:
                if not self.vector_store.registry.get_document(d_id):
                    raise DocumentNotFoundError(f"Document with ID '{d_id}' was not found.")

        target_exts: Optional[Set[str]] = (
            {ext.lower().lstrip(".") for ext in file_extensions} if file_extensions else None
        )

        # 2. Embed question
        query_embedding = self.embedding_service.embed_query(cleaned_question)

        # Candidate pool size for hybrid / MMR / reranking
        candidate_k = max(top_k * 3, 10)

        # 3. Dense Vector Retrieval
        need_embeddings = enable_mmr
        dense_results = self.vector_store.query_similar(
            query_embedding=query_embedding,
            top_k=candidate_k,
            document_ids=target_doc_ids,
            include_embeddings=need_embeddings,
        )

        # Apply extension filter to dense results if specified
        if target_exts:
            filtered_dense = []
            for r in dense_results:
                fname = r.get("filename", "").lower()
                ext = fname.rsplit(".", 1)[-1] if "." in fname else ""
                if ext in target_exts:
                    filtered_dense.append(r)
            dense_results = filtered_dense

        # 4. Hybrid Search (Dense + BM25) if enabled
        if enable_hybrid and self.bm25_service and not self.bm25_service.is_empty():
            bm25_results = self.bm25_service.search(
                query=cleaned_question,
                top_k=candidate_k,
                document_ids=target_doc_ids,
                file_extensions=file_extensions,
            )

            # Combine using Reciprocal Rank Fusion (RRF)
            rrf_scores: Dict[str, float] = {}
            chunk_map: Dict[str, Dict[str, Any]] = {}

            # Dense ranks
            for rank, item in enumerate(dense_results):
                cid = item["chunk_id"]
                chunk_map[cid] = item
                rrf_scores[cid] = rrf_scores.get(cid, 0.0) + hybrid_dense_weight / (60.0 + rank + 1)

            # BM25 ranks
            for rank, item in enumerate(bm25_results):
                cid = item["chunk_id"]
                if cid not in chunk_map:
                    chunk_map[cid] = {
                        "chunk_id": item["chunk_id"],
                        "document_id": item["document_id"],
                        "chunk_index": item["chunk_index"],
                        "filename": item["filename"],
                        "page_number": item.get("page_number"),
                        "char_length": len(item.get("text", "")),
                        "text": item.get("text", ""),
                        "distance": 0.5,
                        "relevance_score": item.get("relevance_score", 0.5),
                    }
                rrf_scores[cid] = rrf_scores.get(cid, 0.0) + hybrid_bm25_weight / (60.0 + rank + 1)

            # Sort by RRF score descending
            sorted_cids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)
            max_rrf = max(rrf_scores.values()) if rrf_scores else 1.0

            combined_chunks: List[RetrievedChunk] = []
            for cid in sorted_cids:
                item = chunk_map[cid]
                norm_score = round(rrf_scores[cid] / max_rrf, 4) if max_rrf > 0 else 0.5
                combined_chunks.append(
                    RetrievedChunk(
                        chunk_id=item["chunk_id"],
                        document_id=item["document_id"],
                        chunk_index=item["chunk_index"],
                        filename=item["filename"],
                        page_number=item.get("page_number"),
                        text=item["text"],
                        relevance_score=norm_score,
                        distance=round(item.get("distance", 1.0 - norm_score), 4),
                    )
                )
            candidates = combined_chunks
        else:
            candidates = [
                RetrievedChunk(
                    chunk_id=r["chunk_id"],
                    document_id=r["document_id"],
                    chunk_index=r["chunk_index"],
                    filename=r["filename"],
                    page_number=r.get("page_number"),
                    text=r["text"],
                    relevance_score=r["relevance_score"],
                    distance=r["distance"],
                )
                for r in dense_results
            ]

        # 5. Semantic MMR Diversification if enabled
        if enable_mmr and candidates:
            # Map candidate embeddings from dense results if available, else compute
            dense_emb_map = {r["chunk_id"]: r.get("embedding") for r in dense_results if r.get("embedding") is not None}
            cand_embeddings = []
            missing_chunks = []
            missing_indices = []

            for idx, c in enumerate(candidates):
                emb = dense_emb_map.get(c.chunk_id)
                if emb is not None and len(emb) == len(query_embedding):
                    cand_embeddings.append(emb)
                else:
                    cand_embeddings.append([])
                    missing_chunks.append(c.text)
                    missing_indices.append(idx)

            if missing_chunks:
                computed = self.embedding_service.embed_documents(missing_chunks)
                for pos, comp_emb in zip(missing_indices, computed):
                    cand_embeddings[pos] = comp_emb

            candidates = maximal_marginal_relevance(
                query_embedding=query_embedding,
                candidate_embeddings=cand_embeddings,
                candidate_chunks=candidates,
                k=top_k if not enable_reranking else candidate_k,
                lambda_mult=mmr_lambda,
            )

        # 6. Cross-Encoder Reranking if enabled
        if enable_reranking and self.reranker:
            candidates = self.reranker.rerank(cleaned_question, candidates, top_k=top_k)
        else:
            candidates = candidates[:top_k]

        return candidates
