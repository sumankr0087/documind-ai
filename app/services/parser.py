"""Document parsing service supporting PDF (via PyMuPDF), TXT, and Markdown."""
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import pymupdf


class ParsingError(Exception):
    """Exception raised when document parsing fails."""
    pass


class UnsupportedFileTypeError(Exception):
    """Exception raised when an unsupported file type is provided."""
    pass


@dataclass
class ExtractedPage:
    """Represents text extracted from a single page or document section."""
    page_number: Optional[int]
    text: str
    char_count: int


@dataclass
class ParsedDocument:
    """Represents the complete parsed document."""
    filename: str
    content_type: str
    pages: List[ExtractedPage]
    total_chars: int

    @property
    def full_text(self) -> str:
        return "\n\n".join(p.text for p in self.pages if p.text.strip())


SUPPORTED_EXTENSIONS = {
    ".pdf": "application/pdf",
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".markdown": "text/markdown",
}


class DocumentParser:
    """Parser for extracting structured text and page metadata from documents."""

    @staticmethod
    def detect_content_type(filename: str, declared_type: Optional[str] = None) -> str:
        """Validate and resolve MIME content type based on extension and declared type."""
        suffix = Path(filename).suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            raise UnsupportedFileTypeError(
                f"Unsupported file format '{suffix}'. Supported formats are: {', '.join(SUPPORTED_EXTENSIONS.keys())}"
            )
        return SUPPORTED_EXTENSIONS[suffix]

    @classmethod
    def parse_pdf(cls, file_bytes: bytes, filename: str) -> ParsedDocument:
        """Extract text page-by-page from PDF using PyMuPDF."""
        pages: List[ExtractedPage] = []
        try:
            doc = pymupdf.open(stream=file_bytes, filetype="pdf")
        except Exception as e:
            raise ParsingError(f"Failed to open PDF document: {e}") from e

        try:
            if doc.is_encrypted:
                raise ParsingError("Encrypted or password-protected PDF files are not supported.")

            for page_idx in range(len(doc)):
                page = doc[page_idx]
                text = page.get_text("text").strip()
                if text:
                    pages.append(
                        ExtractedPage(
                            page_number=page_idx + 1,
                            text=text,
                            char_count=len(text),
                        )
                    )

            if not pages:
                # Document has no text (e.g. scanned images without OCR)
                raise ParsingError(
                    "The PDF document does not contain extractable text. Please ensure it is not an un-OCRed scanned image."
                )

            total_chars = sum(p.char_count for p in pages)
            return ParsedDocument(
                filename=filename,
                content_type="application/pdf",
                pages=pages,
                total_chars=total_chars,
            )
        finally:
            doc.close()

    @classmethod
    def parse_text(cls, file_bytes: bytes, filename: str, content_type: str) -> ParsedDocument:
        """Extract text from plain text or Markdown files."""
        text = ""
        for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
            try:
                text = file_bytes.decode(encoding).strip()
                break
            except UnicodeDecodeError:
                continue

        if not text:
            # Try with replacement
            text = file_bytes.decode("utf-8", errors="replace").strip()

        if not text:
            raise ParsingError("The uploaded text document is empty.")

        pages = [
            ExtractedPage(
                page_number=1,
                text=text,
                char_count=len(text),
            )
        ]

        return ParsedDocument(
            filename=filename,
            content_type=content_type,
            pages=pages,
            total_chars=len(text),
        )

    @classmethod
    def parse(cls, file_bytes: bytes, filename: str, declared_type: Optional[str] = None) -> ParsedDocument:
        """Parse raw file bytes into structured document pages based on file extension."""
        content_type = cls.detect_content_type(filename, declared_type)

        if content_type == "application/pdf":
            return cls.parse_pdf(file_bytes, filename)
        else:
            return cls.parse_text(file_bytes, filename, content_type)
