"""Dependency injection providers for FastAPI routes."""
from typing import Dict, Tuple
from fastapi import Depends
from app.config import Settings, get_settings
from app.services.chunker import TextChunker
from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStoreService
from app.services.retriever import RetrieverService
from app.services.llm import LLMService

_vector_stores: Dict[Tuple[str, str], VectorStoreService] = {}
_embedding_services: Dict[Tuple[str, str], EmbeddingService] = {}


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


def get_retriever_service(
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    vector_store: VectorStoreService = Depends(get_vector_store),
) -> RetrieverService:
    """Return RetrieverService wired with active embedding and vector store."""
    return RetrieverService(embedding_service=embedding_service, vector_store=vector_store)


def get_llm_service(settings: Settings = Depends(get_settings)) -> LLMService:
    """Return configured LLMService."""
    return LLMService(settings=settings)
