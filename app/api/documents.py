from __future__ import annotations
"""Document ingestion, deduplication, batch upload, and management API endpoints."""
import hashlib
import logging
import uuid
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.config import Settings, get_settings
from app.dependencies import (
    get_bm25_service,
    get_chunker,
    get_embedding_service,
    get_sqlite_store,
    get_vector_store,
)
from app.models.document import (
    BatchUploadResponse,
    DocumentDeleteResponse,
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentMetadata,
    DocumentUploadResponse,
)
from app.services.bm25_search import BM25SearchService
from app.services.chunker import TextChunker
from app.services.embeddings import EmbeddingService
from app.services.parser import DocumentParser, ParsingError, UnsupportedFileTypeError
from app.services.sqlite_store import SQLiteStore
from app.services.vector_store import VectorStoreService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


async def _process_single_file(
    file: UploadFile,
    settings: Settings,
    chunker: TextChunker,
    embedding_service: EmbeddingService,
    vector_store: VectorStoreService,
    sqlite_store: SQLiteStore,
    bm25_service: BM25SearchService,
) -> TupleDocumentResult:
    """Internal helper to validate, deduplicate, parse, chunk, embed, and index a file."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is missing or invalid.",
        )

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes).",
        )
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.max_upload_size_mb} MB.",
        )

    # 1. Byte-for-byte deduplication check via SHA-256
    file_hash = hashlib.sha256(content).hexdigest()
    existing_hash_record = sqlite_store.get_document_by_hash(file_hash)
    if existing_hash_record:
        existing_doc = vector_store.registry.get_document(existing_hash_record["document_id"])
        if existing_doc:
            logger.info("Skipping duplicate upload for '%s' (matches '%s')", file.filename, existing_doc.filename)
            return existing_doc, True, f"Duplicate file skipped: identical content already indexed in '{existing_doc.filename}'"

    # 2. Parse document
    try:
        parsed_doc = DocumentParser.parse(content, file.filename, file.content_type)
    except UnsupportedFileTypeError as e:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(e)) from e
    except ParsingError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e
    except Exception as e:
        logger.error("Unexpected error parsing file %s: %s", file.filename, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while parsing the document: {e}",
        ) from e

    # 3. Create document ID and chunk text
    document_id = str(uuid.uuid4())
    chunks = chunker.chunk_document(document_id, parsed_doc)
    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No valid text chunks could be extracted from this document.",
        )

    # 4. Generate embeddings
    chunk_texts = [c.text for c in chunks]
    try:
        embeddings = embedding_service.embed_documents(chunk_texts)
    except Exception as e:
        logger.error("Failed to generate embeddings for %s: %s", file.filename, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate vector embeddings.",
        ) from e

    # 5. Index into ChromaDB
    try:
        vector_store.add_chunks(chunks, embeddings)
    except Exception as e:
        logger.error("Failed to index chunks into ChromaDB: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store vectors in database.",
        ) from e

    # 6. Index into BM25 Keyword Search
    bm25_service.add_chunks(
        [
            {
                "chunk_id": c.chunk_id,
                "document_id": c.document_id,
                "chunk_index": c.chunk_index,
                "filename": c.filename,
                "page_number": c.page_number,
                "text": c.text,
            }
            for c in chunks
        ]
    )

    # 7. Register hash in SQLite for deduplication
    sqlite_store.register_document_hash(file_hash, document_id, file.filename)

    # 8. Save raw file copy
    try:
        save_path = Path(settings.upload_dir) / f"{document_id}_{file.filename}"
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(content)
    except Exception as e:
        logger.warning("Could not save local file copy: %s", e)

    # 9. Record document metadata in registry
    page_count = len(parsed_doc.pages) if parsed_doc.content_type == "application/pdf" else None
    doc_metadata = DocumentMetadata(
        document_id=document_id,
        filename=file.filename,
        content_type=parsed_doc.content_type,
        size_bytes=len(content),
        chunk_count=len(chunks),
        page_count=page_count,
        file_hash=file_hash,
    )
    vector_store.registry.register_document(doc_metadata)

    return doc_metadata, False, f"Document '{file.filename}' successfully ingested and indexed."


# Type alias for internal result
TupleDocumentResult = tuple[DocumentMetadata, bool, str]


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and ingest a document with duplicate detection",
)
async def upload_document(
    file: UploadFile = File(..., description="Document file to upload (PDF, TXT, MD)"),
    settings: Settings = Depends(get_settings),
    chunker: TextChunker = Depends(get_chunker),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    vector_store: VectorStoreService = Depends(get_vector_store),
    sqlite_store: SQLiteStore = Depends(get_sqlite_store),
    bm25_service: BM25SearchService = Depends(get_bm25_service),
) -> DocumentUploadResponse:
    """Ingest a single document: validates file, skips byte-for-byte duplicates, chunks, embeds, and indexes."""
    doc_metadata, skipped, message = await _process_single_file(
        file=file,
        settings=settings,
        chunker=chunker,
        embedding_service=embedding_service,
        vector_store=vector_store,
        sqlite_store=sqlite_store,
        bm25_service=bm25_service,
    )

    return DocumentUploadResponse(
        message=message,
        document=doc_metadata,
        skipped=skipped,
    )


@router.post(
    "/upload-batch",
    response_model=BatchUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and ingest multiple documents simultaneously",
)
async def upload_batch_documents(
    files: List[UploadFile] = File(..., description="Multiple document files (PDF, TXT, MD)"),
    settings: Settings = Depends(get_settings),
    chunker: TextChunker = Depends(get_chunker),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    vector_store: VectorStoreService = Depends(get_vector_store),
    sqlite_store: SQLiteStore = Depends(get_sqlite_store),
    bm25_service: BM25SearchService = Depends(get_bm25_service),
) -> BatchUploadResponse:
    """Upload multiple documents in one batch request with deduplication handling for each file."""
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided in batch upload request.",
        )

    ingested = []
    ingested_count = 0
    skipped_count = 0

    for f in files:
        try:
            doc_metadata, skipped, _ = await _process_single_file(
                file=f,
                settings=settings,
                chunker=chunker,
                embedding_service=embedding_service,
                vector_store=vector_store,
                sqlite_store=sqlite_store,
                bm25_service=bm25_service,
            )
            ingested.append(doc_metadata)
            if skipped:
                skipped_count += 1
            else:
                ingested_count += 1
        except Exception as e:
            logger.error("Failed to process file '%s' in batch: %s", f.filename, e)
            continue

    return BatchUploadResponse(
        message=f"Batch processed {len(files)} files: {ingested_count} ingested, {skipped_count} skipped as duplicates.",
        total_files=len(files),
        ingested_count=ingested_count,
        skipped_count=skipped_count,
        documents=ingested,
    )


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List all indexed documents",
)
def list_documents(
    vector_store: VectorStoreService = Depends(get_vector_store),
) -> DocumentListResponse:
    """Retrieve metadata for all ingested documents."""
    docs = vector_store.registry.list_documents()
    return DocumentListResponse(total_documents=len(docs), documents=docs)


@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
    summary="Get document details and chunk breakdown",
)
def get_document(
    document_id: str,
    vector_store: VectorStoreService = Depends(get_vector_store),
) -> DocumentDetailResponse:
    """Retrieve document metadata and list of all its constituent chunks."""
    doc = vector_store.registry.get_document(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found.",
        )

    chunks = vector_store.get_chunks_for_document(document_id)
    return DocumentDetailResponse(document=doc, chunks=chunks)


@router.delete(
    "/{document_id}",
    response_model=DocumentDeleteResponse,
    summary="Delete a document, its vectors, and its hash mapping",
)
def delete_document(
    document_id: str,
    settings: Settings = Depends(get_settings),
    vector_store: VectorStoreService = Depends(get_vector_store),
    sqlite_store: SQLiteStore = Depends(get_sqlite_store),
    bm25_service: BM25SearchService = Depends(get_bm25_service),
) -> DocumentDeleteResponse:
    """Delete a document, its metadata, its chunks from ChromaDB, its BM25 index entries, and its deduplication hash."""
    doc = vector_store.registry.get_document(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found.",
        )

    # 1. Delete vectors from ChromaDB
    chunks_deleted = vector_store.delete_document_chunks(document_id)

    # 2. Delete from BM25 Index
    bm25_service.delete_document_chunks(document_id)

    # 3. Delete deduplication hash from SQLite
    sqlite_store.delete_hash_by_document_id(document_id)

    # 4. Clean up uploaded raw file if present
    upload_dir = Path(settings.upload_dir)
    for f in upload_dir.glob(f"{document_id}_*"):
        try:
            f.unlink()
        except Exception as e:
            logger.warning("Failed to delete local raw file %s: %s", f, e)

    return DocumentDeleteResponse(
        message=f"Document '{doc.filename}' ({document_id}) successfully deleted.",
        document_id=document_id,
        chunks_deleted=chunks_deleted,
    )
