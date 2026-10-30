"""Test fixtures and configurations for DocuMind AI test suite."""
import os
import shutil
import tempfile
import pytest
import pymupdf
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.dependencies import (
    get_bm25_service,
    get_chunker,
    get_embedding_service,
    get_sqlite_store,
    get_vector_store,
)
from app.main import app
from app.services.bm25_search import BM25SearchService
from app.services.chunker import TextChunker
from app.services.embeddings import EmbeddingService
from app.services.sqlite_store import SQLiteStore
from app.services.vector_store import VectorStoreService


@pytest.fixture
def test_settings():
    """Provide isolated per-test settings with dedicated temp storage and SQLite database."""
    temp_dir = tempfile.mkdtemp(prefix="documind_test_case_")
    settings = Settings(
        app_env="testing",
        chroma_persist_directory=os.path.join(temp_dir, "chroma"),
        chroma_collection_name="test_collection",
        upload_dir=os.path.join(temp_dir, "uploads"),
        sqlite_db_path=os.path.join(temp_dir, "documind_test.db"),
        max_upload_size_mb=5,
        llm_provider="mock",
        openai_api_key="mock-key",
        chunk_size=300,
        chunk_overlap=50,
        top_k=5,
    )
    yield settings
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def test_client(test_settings):
    """FastAPI TestClient with isolated test settings and dependencies."""
    app.dependency_overrides[get_settings] = lambda: test_settings
    vector_store = VectorStoreService(
        persist_directory=test_settings.chroma_persist_directory,
        collection_name=test_settings.chroma_collection_name,
    )
    app.dependency_overrides[get_vector_store] = lambda: vector_store
    app.dependency_overrides[get_chunker] = lambda: TextChunker(
        chunk_size=test_settings.chunk_size, chunk_overlap=test_settings.chunk_overlap
    )
    sqlite_store = SQLiteStore(db_path=test_settings.sqlite_db_path)
    app.dependency_overrides[get_sqlite_store] = lambda: sqlite_store
    bm25_service = BM25SearchService()
    app.dependency_overrides[get_bm25_service] = lambda: bm25_service

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Generate in-memory multi-page PDF bytes using PyMuPDF for testing."""
    doc = pymupdf.open()

    # Page 1
    page1 = doc.new_page()
    page1.insert_text(
        pymupdf.Point(50, 72),
        "DocuMind AI Architecture Guide\n\nDocuMind AI is a modern Document Q&A platform built with FastAPI and ChromaDB. "
        "It uses PyMuPDF for high performance PDF extraction and Sentence Transformers for dense vector representations.",
    )

    # Page 2
    page2 = doc.new_page()
    page2.insert_text(
        pymupdf.Point(50, 72),
        "Deployment and Containerization\n\nThe service is containerized using Docker and deployed on cloud infrastructure. "
        "It supports twelve-factor configuration through environment variables and provides a health check at /health.",
    )

    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes


@pytest.fixture
def sample_txt_bytes() -> bytes:
    """Generate sample plain text document."""
    return (
        "DocuMind AI Plain Text Reference\n\n"
        "Sentence Transformers generate high-quality dense vector embeddings from unstructured text. "
        "Cosine similarity measures the angle between vectors, providing normalized relevance scores between 0 and 1."
    ).encode("utf-8")


@pytest.fixture
def sample_md_bytes() -> bytes:
    """Generate sample markdown document."""
    return (
        "# Markdown Specification\n\n"
        "## Chunking and Retrieval\n"
        "Sliding window chunking prevents context fragmentation at sentence boundaries. "
        "Top-5 chunks are passed to the language model to generate grounded answers with source citations."
    ).encode("utf-8")
