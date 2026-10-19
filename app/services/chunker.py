"""Text chunking service with configurable chunk size, overlap, and page-aware tracking."""
from dataclasses import dataclass
from typing import List, Optional
from app.services.parser import ParsedDocument


@dataclass
class TextChunk:
    """Represents a discrete text chunk prepared for vector indexing."""
    chunk_id: str
    document_id: str
    chunk_index: int
    filename: str
    page_number: Optional[int]
    text: str
    char_length: int


class TextChunker:
    """Splits parsed document pages into overlapping text chunks."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be strictly less than chunk_size")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def _split_text_with_overlap(self, text: str) -> List[str]:
        """Split a long text string into overlapping chunks honoring word boundaries where possible."""
        cleaned_text = " ".join(text.split())
        if not cleaned_text:
            return []

        if len(cleaned_text) <= self.chunk_size:
            return [cleaned_text]

        chunks = []
        start = 0
        text_len = len(cleaned_text)

        while start < text_len:
            end = start + self.chunk_size

            if end >= text_len:
                chunks.append(cleaned_text[start:text_len])
                break

            # Find a word boundary (space) near the end to avoid cutting words in half
            space_idx = cleaned_text.rfind(" ", start, end)
            if space_idx > start + (self.chunk_size // 2):
                chunk = cleaned_text[start:space_idx]
                start = space_idx + 1 - self.chunk_overlap
            else:
                chunk = cleaned_text[start:end]
                start = end - self.chunk_overlap

            # Ensure start progresses forward
            if start <= 0 or start <= (len(chunks) > 0 and len(" ".join(chunks[:len(chunks)-1])) or 0):
                start = end - self.chunk_overlap

            chunks.append(chunk)

            # Prevent infinite loop if overlap equals or exceeds step
            step = len(chunk) - self.chunk_overlap
            if step <= 0:
                start += self.chunk_size

        return [c.strip() for c in chunks if c.strip()]

    def chunk_document(self, document_id: str, parsed_doc: ParsedDocument) -> List[TextChunk]:
        """Split all pages of a parsed document into structured TextChunks with metadata."""
        chunks: List[TextChunk] = []
        chunk_index = 0

        for page in parsed_doc.pages:
            page_text = page.text.strip()
            if not page_text:
                continue

            split_snippets = self._split_text_with_overlap(page_text)
            for snippet in split_snippets:
                chunk_id = f"{document_id}_chunk_{chunk_index}"
                chunks.append(
                    TextChunk(
                        chunk_id=chunk_id,
                        document_id=document_id,
                        chunk_index=chunk_index,
                        filename=parsed_doc.filename,
                        page_number=page.page_number,
                        text=snippet,
                        char_length=len(snippet),
                    )
                )
                chunk_index += 1

        return chunks
