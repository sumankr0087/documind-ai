"""Document ingestion and management API endpoints."""
import logging
import uuid
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.config import Settings, get_settings
from app.dependencies import get_chunker, get_embedding_service, get_vector_store
from app.models.document import (
    DocumentDeleteResponse,
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentMetadata,
    DocumentUploadResponse,
)
from app.services.chunker import TextChunker
from app.services.embeddings import EmbeddingService
from app.services.parser import DocumentParser, ParsingError, UnsupportedFileTypeError
from app.services.vector_store import VectorStoreService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and ingest a document",
)
async def upload_document(
    file: UploadFile = File(..., description="Document file to upload (PDF, TXT, MD)"),
    settings: Settings = Depends(get_settings),
    chunker: TextChunker = Depends(get_chunker),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    vector_store: VectorStoreService = Depends(get_vector_store),
) -> DocumentUploadResponse:
    """Ingest a document: validates file, extracts text, chunks, embeds, and indexes into ChromaDB."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is missing or invalid.",
        )

    # 1. Read file bytes and validate size
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

    # 6. Save raw file copy for reference
    try:
        save_path = Path(settings.upload_dir) / f"{document_id}_{file.filename}"
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(content)
    except Exception as e:
        logger.warning("Could not save local file copy: %s", e)

    # 7. Record document metadata in registry
    page_count = len(parsed_doc.pages) if parsed_doc.content_type == "application/pdf" else None
    doc_metadata = DocumentMetadata(
        document_id=document_id,
        filename=file.filename,
        content_type=parsed_doc.content_type,
        size_bytes=len(content),
        chunk_count=len(chunks),
        page_count=page_count,
    )
    vector_store.registry.register_document(doc_metadata)

    return DocumentUploadResponse(
        message=f"Document '{file.filename}' successfully ingested and indexed.",
        document=doc_metadata,
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
    summary="Delete a document and its vectors",
)
def delete_document(
    document_id: str,
    settings: Settings = Depends(get_settings),
    vector_store: VectorStoreService = Depends(get_vector_store),
) -> DocumentDeleteResponse:
    """Delete a document, its metadata, and all its chunks from the vector store."""
    doc = vector_store.registry.get_document(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found.",
        )

    chunks_deleted = vector_store.delete_document_chunks(document_id)

    # Clean up uploaded raw file if present
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
