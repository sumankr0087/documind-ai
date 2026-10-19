# DocuMind AI System Overview

DocuMind AI is an enterprise-grade Document Question & Answering platform powered by Retrieval-Augmented Generation (RAG).

## Key Capabilities
1. Multi-Format Ingestion: Accepts PDF documents (via PyMuPDF), Markdown files, and plain text files.
2. Semantic Chunking: Splits incoming documents into overlapping text chunks to preserve cross-sentence continuity.
3. Dense Vector Search: Converts chunks and search queries into normalized 384-dimensional embeddings using Sentence Transformers (all-MiniLM-L6-v2) and stores them in ChromaDB.
4. Grounded Question Answering: Retrieves top-5 relevant chunks, verifies factual evidence sufficiency, and returns answers with precise source citations including document filename, page number, and chunk ID.
5. Prompt Injection Defense: Uses XML context boundaries and strict system directives to prevent adversarial documents from altering system behavior.
