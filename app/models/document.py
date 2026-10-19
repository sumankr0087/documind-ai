"""Document data models and schemas."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ChunkMetadata(BaseModel):
    """Metadata for an individual text chunk."""

    chunk_id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="Parent document identifier")
    chunk_index: int = Field(..., description="0-indexed position within document")
    filename: str = Field(..., description="Original filename")
    page_number: Optional[int] = Field(None, description="Page number (1-indexed for PDF)")
    char_length: int = Field(..., description="Length of chunk text in characters")


class ChunkDetail(BaseModel):
    """Detailed representation of a document chunk."""

    chunk_id: str
    document_id: str
    chunk_index: int
    filename: str
    page_number: Optional[int] = None
    text: str


class DocumentMetadata(BaseModel):
    """Metadata stored for a processed document."""

    document_id: str = Field(..., description="Unique document UUID")
    filename: str = Field(..., description="Original uploaded filename")
    content_type: str = Field(..., description="Detected MIME type (application/pdf, text/plain, text/markdown)")
    size_bytes: int = Field(..., description="Size of the uploaded file in bytes")
    chunk_count: int = Field(..., description="Number of chunks extracted and indexed")
    page_count: Optional[int] = Field(None, description="Total number of pages (for PDF)")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class DocumentUploadResponse(BaseModel):
    """Response returned upon successful document upload and indexing."""

    message: str = "Document successfully ingested and indexed"
    document: DocumentMetadata


class DocumentListResponse(BaseModel):
    """Response returned when listing all ingested documents."""

    total_documents: int
    documents: List[DocumentMetadata]


class DocumentDetailResponse(BaseModel):
    """Response returned when querying a specific document by ID."""

    document: DocumentMetadata
    chunks: List[ChunkMetadata]


class DocumentDeleteResponse(BaseModel):
    """Response returned upon document deletion."""

    message: str
    document_id: str
    chunks_deleted: int
