"""Dependency injection providers for FastAPI routes."""
from typing import Dict, Optional, Tuple
from fastapi import Depends
from app.config import Settings, get_settings
from app.services.chunker import TextChunker
from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStoreService
from app.services.retriever import RetrieverService
from app.services.llm import LLMService
from app.services.sqlite_store import SQLiteStore
from app.services.bm25_search import BM25SearchService
from app.services.reranker import CrossEncoderReranker

_vector_stores: Dict[Tuple[str, str], VectorStoreService] = {}
_embedding_services: Dict[Tuple[str, str], EmbeddingService] = {}
_sqlite_stores: Dict[str, SQLiteStore] = {}
_bm25_service: Optional[BM25SearchService] = None
_reranker_service: Optional[CrossEncoderReranker] = None


def get_chunker(settings: Settings = Depends(get_settings)) -> TextChunker:
    """Return configured TextChunker instance."""
    return TextChunker(chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap)


def get_embedding_service(settings: Settings = Depends(get_settings)) -> EmbeddingService:
    """Return cached EmbeddingService for given model and device."""
    key = (settings.embedding_model_name, settings.embedding_device)
    if key not in _embedding_services:
        _embedding_services[key] = EmbeddingService(
            model_name=settings.embedding_model_name,
            device=settings.embedding_device,
        )
    return _embedding_services[key]


def get_vector_store(settings: Settings = Depends(get_settings)) -> VectorStoreService:
    """Return cached VectorStoreService for given directory and collection."""
    key = (settings.chroma_persist_directory, settings.chroma_collection_name)
    if key not in _vector_stores:
        _vector_stores[key] = VectorStoreService(
            persist_directory=settings.chroma_persist_directory,
            collection_name=settings.chroma_collection_name,
        )
    return _vector_stores[key]


def get_sqlite_store(settings: Settings = Depends(get_settings)) -> SQLiteStore:
    """Return cached SQLiteStore instance."""
    if settings.sqlite_db_path not in _sqlite_stores:
        _sqlite_stores[settings.sqlite_db_path] = SQLiteStore(db_path=settings.sqlite_db_path)
    return _sqlite_stores[settings.sqlite_db_path]


def get_bm25_service(
    vector_store: VectorStoreService = Depends(get_vector_store),
) -> BM25SearchService:
    """Return singleton BM25SearchService synchronized with vector store."""
    global _bm25_service
    if _bm25_service is None:
        _bm25_service = BM25SearchService()
        all_chunks = vector_store.get_all_chunks()
        if all_chunks:
            _bm25_service.rebuild_index(all_chunks)
    return _bm25_service


def get_reranker_service(settings: Settings = Depends(get_settings)) -> CrossEncoderReranker:
    """Return singleton CrossEncoderReranker instance."""
    global _reranker_service
    if _reranker_service is None:
        _reranker_service = CrossEncoderReranker(
            model_name=settings.reranker_model_name,
            device=settings.embedding_device,
        )
    return _reranker_service


def get_retriever_service(
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    vector_store: VectorStoreService = Depends(get_vector_store),
    bm25_service: BM25SearchService = Depends(get_bm25_service),
    reranker: CrossEncoderReranker = Depends(get_reranker_service),
) -> RetrieverService:
    """Return RetrieverService wired with active embedding, vector store, BM25, and reranker."""
    return RetrieverService(
        embedding_service=embedding_service,
        vector_store=vector_store,
        bm25_service=bm25_service,
        reranker=reranker,
    )


def get_llm_service(settings: Settings = Depends(get_settings)) -> LLMService:
    """Return configured LLMService."""
    return LLMService(settings=settings)

