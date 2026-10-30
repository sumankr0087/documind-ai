"""ChromaDB Vector Store wrapper with document filtering, indexing, and persistence."""
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.services.chunker import TextChunk
from app.models.document import DocumentMetadata, ChunkMetadata

logger = logging.getLogger(__name__)


class DocumentRegistry:
    """Manages metadata registry for all uploaded documents."""

    def __init__(self, storage_path: str):
        self.file_path = Path(storage_path) / "documents_registry.json"
        self._ensure_file()

    def _ensure_file(self) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump({}, f)

    def _load(self) -> Dict[str, Dict[str, Any]]:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save(self, data: Dict[str, Dict[str, Any]]) -> None:
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def register_document(self, metadata: DocumentMetadata) -> None:
        data = self._load()
        data[metadata.document_id] = metadata.model_dump()
        self._save(data)

    def get_document(self, document_id: str) -> Optional[DocumentMetadata]:
        data = self._load()
        doc_dict = data.get(document_id)
        if doc_dict:
            return DocumentMetadata(**doc_dict)
        return None

    def list_documents(self) -> List[DocumentMetadata]:
        data = self._load()
        docs = [DocumentMetadata(**item) for item in data.values()]
        # Sort by creation timestamp descending
        docs.sort(key=lambda d: d.created_at, reverse=True)
        return docs

    def delete_document(self, document_id: str) -> bool:
        data = self._load()
        if document_id in data:
            del data[document_id]
            self._save(data)
            return True
        return False


class VectorStoreService:
    """Service wrapping ChromaDB operations."""

    def __init__(self, persist_directory: str = "./data/chroma", collection_name: str = "documind_collection"):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        Path(persist_directory).mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False, is_persistent=True),
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        self.registry = DocumentRegistry(persist_directory)

    def add_chunks(self, chunks: List[TextChunk], embeddings: List[List[float]]) -> None:
        """Add text chunks and corresponding embeddings into ChromaDB."""
        if not chunks:
            return

        ids = [c.chunk_id for c in chunks]
        documents = [c.text for c in chunks]
        metadatas = [
            {
                "document_id": c.document_id,
                "chunk_index": c.chunk_index,
                "filename": c.filename,
                "page_number": c.page_number if c.page_number is not None else -1,
                "char_length": c.char_length,
            }
            for c in chunks
        ]

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        logger.info("Successfully indexed %d chunks in collection '%s'", len(chunks), self.collection_name)

    def query_similar(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        document_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
        include_embeddings: bool = False,
    ) -> List[Dict[str, Any]]:
        """Retrieve the top-K similar chunks, optionally filtered by single or multiple document IDs."""
        total_count = self.collection.count()
        if total_count == 0:
            return []

        # Chroma requires n_results <= total collection count
        n_results = min(top_k, total_count)
        if n_results <= 0:
            return []

        where_filter = None
        if document_ids:
            clean_ids = [d for d in document_ids if d]
            if len(clean_ids) == 1:
                where_filter = {"document_id": clean_ids[0]}
            elif len(clean_ids) > 1:
                where_filter = {"document_id": {"$in": clean_ids}}
        elif document_id:
            where_filter = {"document_id": document_id}

        includes = ["documents", "metadatas", "distances"]
        if include_embeddings:
            includes.append("embeddings")

        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_filter,
                include=includes,
            )
        except Exception as e:
            logger.warning("Chroma query failed: %s", e)
            return []

        chunks: List[Dict[str, Any]] = []
        if not results or not results.get("ids") or not results["ids"][0]:
            return []

        ids = results["ids"][0]
        documents = results["documents"][0] if results.get("documents") else []
        metadatas = results["metadatas"][0] if results.get("metadatas") else []
        distances = results["distances"][0] if results.get("distances") else []
        embeddings = results.get("embeddings", [[]])[0] if include_embeddings and results.get("embeddings") else []

        for i in range(len(ids)):
            chunk_id = ids[i]
            text = documents[i] if i < len(documents) else ""
            meta = metadatas[i] if i < len(metadatas) else {}
            dist = distances[i] if i < len(distances) else 1.0

            # For cosine distance: distance is 1 - cosine_similarity. So similarity = 1 - distance
            # Clamp between 0.0 and 1.0
            similarity = max(0.0, min(1.0, 1.0 - dist))

            page_num = meta.get("page_number", -1)
            chunk_item = {
                "chunk_id": chunk_id,
                "document_id": meta.get("document_id", ""),
                "chunk_index": meta.get("chunk_index", 0),
                "filename": meta.get("filename", ""),
                "page_number": page_num if page_num != -1 else None,
                "char_length": meta.get("char_length", len(text)),
                "text": text,
                "relevance_score": round(similarity, 4),
                "distance": round(dist, 4),
            }
            if include_embeddings and i < len(embeddings):
                chunk_item["embedding"] = embeddings[i]

            chunks.append(chunk_item)

        return chunks

    def get_all_chunks(self) -> List[Dict[str, Any]]:
        """Retrieve all indexed chunks from ChromaDB for lexical index synchronization."""
        total = self.collection.count()
        if total == 0:
            return []

        try:
            results = self.collection.get(include=["documents", "metadatas"])
            if not results or not results.get("ids"):
                return []

            ids = results["ids"]
            docs = results.get("documents", []) or []
            metas = results.get("metadatas", []) or []

            chunks = []
            for i in range(len(ids)):
                m = metas[i] if i < len(metas) else {}
                page_num = m.get("page_number", -1)
                text = docs[i] if i < len(docs) else ""
                chunks.append(
                    {
                        "chunk_id": ids[i],
                        "document_id": m.get("document_id", ""),
                        "chunk_index": m.get("chunk_index", 0),
                        "filename": m.get("filename", ""),
                        "page_number": page_num if page_num != -1 else None,
                        "text": text,
                    }
                )
            return chunks
        except Exception as e:
            logger.warning("Failed to fetch all chunks from ChromaDB: %s", e)
            return []

    def get_chunks_for_document(self, document_id: str) -> List[ChunkMetadata]:
        """Fetch metadata for all chunks belonging to a document."""
        try:
            result = self.collection.get(
                where={"document_id": document_id},
                include=["metadatas"],
            )
        except Exception as e:
            logger.error("Failed to get chunks for document %s: %s", document_id, e)
            return []

        if not result or not result.get("ids"):
            return []

        chunk_list: List[ChunkMetadata] = []
        ids = result["ids"]
        metas = result.get("metadatas", []) or []

        for i, cid in enumerate(ids):
            m = metas[i] if i < len(metas) else {}
            page_num = m.get("page_number", -1)
            chunk_list.append(
                ChunkMetadata(
                    chunk_id=cid,
                    document_id=m.get("document_id", document_id),
                    chunk_index=m.get("chunk_index", i),
                    filename=m.get("filename", ""),
                    page_number=page_num if page_num != -1 else None,
                    char_length=m.get("char_length", 0),
                )
            )

        # Sort chunks by chunk_index
        chunk_list.sort(key=lambda c: c.chunk_index)
        return chunk_list

    def delete_document_chunks(self, document_id: str) -> int:
        """Delete all chunks for a document from vector collection."""
        existing = self.get_chunks_for_document(document_id)
        if not existing:
            return 0

        chunk_ids = [c.chunk_id for c in existing]
        try:
            self.collection.delete(ids=chunk_ids)
        except Exception as e:
            logger.error("Failed to delete chunks for %s: %s", document_id, e)
            raise

        # Also remove from registry
        self.registry.delete_document(document_id)
        return len(chunk_ids)

    def count(self) -> int:
        """Return total number of chunks currently stored in the collection."""
        return self.collection.count()
