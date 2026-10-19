"""Automated tests for text extraction (PyMuPDF, TXT, MD) and chunking services."""
import pytest
from app.services.parser import (
    DocumentParser,
    ParsingError,
    UnsupportedFileTypeError,
    ParsedDocument,
    ExtractedPage,
)
from app.services.chunker import TextChunker


def test_detect_content_type_valid():
    """Verify supported document extensions are mapped correctly."""
    assert DocumentParser.detect_content_type("doc.pdf") == "application/pdf"
    assert DocumentParser.detect_content_type("notes.txt") == "text/plain"
    assert DocumentParser.detect_content_type("README.md") == "text/markdown"
    assert DocumentParser.detect_content_type("guide.markdown") == "text/markdown"


def test_detect_content_type_unsupported():
    """Verify unsupported file extensions raise UnsupportedFileTypeError."""
    with pytest.raises(UnsupportedFileTypeError):
        DocumentParser.detect_content_type("data.csv")

    with pytest.raises(UnsupportedFileTypeError):
        DocumentParser.detect_content_type("script.py")

    with pytest.raises(UnsupportedFileTypeError):
        DocumentParser.detect_content_type("binary.exe")


def test_parse_text(sample_txt_bytes):
    """Verify plain text document parsing."""
    parsed = DocumentParser.parse(sample_txt_bytes, "sample.txt")
    assert parsed.filename == "sample.txt"
    assert parsed.content_type == "text/plain"
    assert len(parsed.pages) == 1
    assert parsed.pages[0].page_number == 1
    assert "Sentence Transformers" in parsed.full_text


def test_parse_markdown(sample_md_bytes):
    """Verify markdown document parsing."""
    parsed = DocumentParser.parse(sample_md_bytes, "guide.md")
    assert parsed.filename == "guide.md"
    assert parsed.content_type == "text/markdown"
    assert len(parsed.pages) == 1
    assert "Sliding window chunking" in parsed.full_text


def test_parse_pdf(sample_pdf_bytes):
    """Verify PyMuPDF multi-page PDF parsing."""
    parsed = DocumentParser.parse(sample_pdf_bytes, "document.pdf")
    assert parsed.filename == "document.pdf"
    assert parsed.content_type == "application/pdf"
    assert len(parsed.pages) == 2
    assert parsed.pages[0].page_number == 1
    assert parsed.pages[1].page_number == 2
    assert "DocuMind AI Architecture" in parsed.pages[0].text
    assert "Deployment and Containerization" in parsed.pages[1].text


def test_parse_empty_document():
    """Verify empty document parsing raises ParsingError."""
    with pytest.raises(ParsingError):
        DocumentParser.parse(b"", "empty.txt")


def test_chunker_validation():
    """Verify chunker parameter validations."""
    with pytest.raises(ValueError, match="chunk_size must be positive"):
        TextChunker(chunk_size=0, chunk_overlap=10)

    with pytest.raises(ValueError, match="chunk_overlap cannot be negative"):
        TextChunker(chunk_size=200, chunk_overlap=-5)

    with pytest.raises(ValueError, match="chunk_overlap must be strictly less than chunk_size"):
        TextChunker(chunk_size=200, chunk_overlap=200)


def test_chunker_splitting(sample_pdf_bytes):
    """Verify chunker produces overlapping chunks with page metadata."""
    parsed = DocumentParser.parse(sample_pdf_bytes, "document.pdf")
    chunker = TextChunker(chunk_size=120, chunk_overlap=30)
    chunks = chunker.chunk_document("doc_123", parsed)

    assert len(chunks) >= 2
    for c in chunks:
        assert c.document_id == "doc_123"
        assert c.filename == "document.pdf"
        assert c.page_number in (1, 2)
        assert len(c.text) > 0
        assert c.chunk_id.startswith("doc_123_chunk_")
