"""Retriever service for semantic similarity search with document filtering."""
import logging
from dataclasses import dataclass
from typing import List, Optional
from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStoreService

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


class RetrieverService:
    """Orchestrates query embedding and vector similarity search."""

    def __init__(self, embedding_service: EmbeddingService, vector_store: VectorStoreService):
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    def retrieve(
        self,
        question: str,
        top_k: int = 5,
        document_id: Optional[str] = None,
    ) -> List[RetrievedChunk]:
        """Retrieve the top-K relevant chunks for a question, optionally scoped to a document."""
        cleaned_question = question.strip()
        if not cleaned_question:
            return []

        # If a specific document_id is provided, verify document exists
        if document_id:
            existing_doc = self.vector_store.registry.get_document(document_id)
            if not existing_doc:
                raise DocumentNotFoundError(f"Document with ID '{document_id}' was not found.")

        # Embed question
        query_embedding = self.embedding_service.embed_query(cleaned_question)

        # Query vector store
        raw_results = self.vector_store.query_similar(
            query_embedding=query_embedding,
            top_k=top_k,
            document_id=document_id,
        )

        chunks: List[RetrievedChunk] = []
        for r in raw_results:
            chunks.append(
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
            )

        return chunks
