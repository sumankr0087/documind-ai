---
title: DocuMind AI
emoji: 🧠
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# DocuMind AI - Intelligent Document RAG Engine

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![Hugging Face Spaces](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces-yellow)](https://huggingface.co/spaces/Sumankr0087/documind-ai)
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/sumankr0087/documind-ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

DocuMind AI is a production-grade **Retrieval-Augmented Generation (RAG)** platform designed for high-accuracy document Question & Answering. It integrates high-speed document extraction (PyMuPDF for PDF, plus TXT and Markdown), overlapping semantic chunking, dense vector representations via Sentence Transformers, persistent vector indexing with ChromaDB, BM25 keyword retrieval, Maximal Marginal Relevance (MMR) diversification, cross-encoder reranking, and grounded LLM synthesis with real-time SSE token streaming, strict source citations (filename, page numbers, and chunk IDs), multi-turn conversation memory in SQLite, and prompt injection defense.

---

## Key Features

1. **Multi-Format Batch Ingestion:** Upload and index multiple PDF, TXT, and Markdown documents simultaneously.
2. **Byte-for-Byte Deduplication:** SHA-256 byte hashing detects and skips duplicate uploads, preventing document dilution.
3. **Advanced Retrieval Pipeline:**
   - **Dense Semantic Retrieval:** `sentence-transformers/all-MiniLM-L6-v2` dense embeddings.
   - **Semantic MMR (Maximal Marginal Relevance):** Balances relevance and content diversity ($\lambda=0.7$).
   - **Hybrid Search:** Combines dense vector retrieval with BM25 keyword matching via Reciprocal Rank Fusion (RRF).
   - **Cross-Encoder Reranking:** Deep contextual passage reranking using `cross-encoder/ms-marco-MiniLM-L-6-v2`.
4. **Targeted Scoping:** Select exact document(s) to search before asking a question, or filter retrieval by file extension (`.pdf`, `.txt`, `.md`).
5. **Real-Time Streaming:** Server-Sent Events (`POST /questions/ask-stream`) deliver tokens as the model generates them.
6. **Chat Topics & SQLite Session History:** Store chat topics in SQLite, reopen previous conversations, and feed recent conversational context into the LLM.
7. **Interactive CLI & Web Studio:** Use the platform via the command-line interface (`python -m app.cli`) or the responsive React Web Studio.
8. **Automated Offline Retrieval Evaluation:** Benchmark hit rate@K, recall@K, and MRR across all retrieval configurations without paid LLM credentials.
9. **Zero-Cost Deployment:** Runs completely free in Docker on Hugging Face Spaces (Port 7860) or Render.

---

## Architecture Overview

```
                   ┌──────────────────────────────────────┐
                   │    React Frontend UI (Web Studio)    │
                   │  - DocumentManager & Multi-Uploader  │
                   │  - Topic Sidebar & ChatInterface     │
                   │  - Real-Time SSE Token Streaming     │
                   │  - Multi-Doc Selector & CitationCard │
                   └──────────────────┬───────────────────┘
                                      │
                         HTTP REST & SSE API Requests
                                      │
                                      ▼
               ┌──────────────────────────────────────────────┐
               │         FastAPI Web Application (app)        │
               │  - /health                                   │
               │  - /documents/upload, /upload-batch, /{id}   │
               │  - /questions/ask, /questions/ask-stream     │
               │  - /chat/sessions (SQLite persistence)       │
               └──────────┬────────────────────────┬──────────┘
                          │                        │
       Ingestion Pipeline │                        │ Query & Retrieval Pipeline
                          ▼                        ▼
               ┌─────────────────────┐   ┌───────────────────────────────┐
               │   DocumentParser    │   │       RetrieverService        │
               │  - PyMuPDF (PDF)    │   │  1. Dense ChromaDB Search     │
               │  - Plain Text & MD  │   │  2. BM25 Keyword Search (RRF) │
               │  - SHA-256 Dedup    │   │  3. Semantic MMR Diversity    │
               └──────────┬──────────┘   │  4. Cross-Encoder Reranker    │
                          ▼              └───────────────┬───────────────┘
               ┌─────────────────────┐                   │
               │     TextChunker     │                   ▼
               │  - Overlapping text │   ┌───────────────────────────────┐
               │  - Page tracking    │   │     ChromaDB + SQLite Store   │
               └──────────┬──────────┘   │  - Persistent HNSW Vectors    │
                          ▼              │  - SHA-256 Document Hashes    │
        ┌─────────────────────────────┐  │  - Topics & Message History   │
        │ Embedding & Ingestion Layer │  └───────────────┬───────────────┘
        │ - all-MiniLM-L6-v2 (384-d)  │                  │ Grounded Context
        │ - BM25 In-Memory Inverted   │                  ▼
        └─────────────────────────────┘  ┌───────────────────────────────┐
                                         │          LLMService           │
                                         │  - Grounded prompt (XML)      │
                                         │  - Real-time token streaming  │
                                         │  - Evidence sufficiency check │
                                         │  - OpenAI / Groq / Ollama /   │
                                         │    Offline Extractive fallback│
                                         └───────────────┬───────────────┘
                                                         │
                                                         ▼
                                            Structured Answer + Citations
                                      (Filename, Page Number, Chunk ID, Score)
```

---

## Technology Stack

- **Frontend UI:** React 18, TypeScript, Vite, Tailwind-style Clean UI, Lucide Icons, OOP Service Layer & Domain Models
- **API Framework:** FastAPI, Uvicorn (ASGI)
- **Document Parsing:** PyMuPDF (`pymupdf`) for native multi-page PDF text extraction, Python UTF-8 parser for TXT/MD
- **Vector Storage:** ChromaDB with persistent HNSW index and cosine similarity
- **BM25 Search:** `rank_bm25` with Reciprocal Rank Fusion (RRF)
- **Embedding Model:** Sentence Transformers (`sentence-transformers/all-MiniLM-L6-v2`, 384 dimensions)
- **Reranker Model:** `cross-encoder/ms-marco-MiniLM-L-6-v2`
- **Session & History Storage:** SQLite3 (`data/documind.db`)
- **LLM Integration:** Configurable via OpenAI-compatible API (OpenAI GPT-4o-mini, Groq, Together, Ollama) and offline extractive fallback
- **Validation & Serialization:** Pydantic v2 & Pydantic-Settings
- **Automated Testing:** Pytest, pytest-asyncio, HTTPX
- **Containerization & Deployment:** Docker, Hugging Face Spaces, Render

---

## Directory Structure

```
documind-ai/
├── frontend/                  # React + TypeScript Web Studio (OOP Architecture)
│   ├── src/
│   │   ├── models/            # Domain Entities: DocumentModel, ChunkModel, CitationModel, ChatSessionModel
│   │   ├── services/          # OOP Service Layer: DocumentService, QuestionService, ChatService, HealthService
│   │   ├── hooks/             # Custom Hooks: useDocuments, useQuestionAnswering, useSystemHealth
│   │   ├── components/        # Components: FileUploader, ChatInterface, CitationCard, SystemHealthBadge
│   │   ├── types/             # TypeScript API interfaces
│   │   ├── App.tsx            # Main Application Layout
│   │   └── index.css          # Design System
│   ├── package.json
│   └── vite.config.ts
├── app/
│   ├── api/
│   │   ├── chat.py            # Chat topic sessions & history endpoints
│   │   ├── documents.py       # Batch upload, list, detail, and deletion with deduplication
│   │   ├── health.py          # GET /health endpoint
│   │   └── questions.py       # POST /questions/ask and /questions/ask-stream endpoints
│   ├── models/
│   │   ├── chat.py            # Chat session and message schemas
│   │   ├── document.py        # Document & batch upload schemas
│   │   ├── health.py          # Health check schema
│   │   └── question.py        # Question request/response schemas & Citations
│   ├── services/
│   │   ├── bm25_search.py     # BM25 keyword search with extension & doc filtering
│   │   ├── chunker.py         # Overlapping text chunker
│   │   ├── embeddings.py      # Sentence Transformers embedding service
│   │   ├── llm.py             # Configurable LLM, token streaming & prompt defense
│   │   ├── parser.py          # PyMuPDF, TXT, and Markdown parser
│   │   ├── reranker.py        # Cross-Encoder passage reranker
│   │   ├── retriever.py       # Dense, MMR, Hybrid, and Cross-Encoder retrieval
│   │   ├── sqlite_store.py    # SQLite database for deduplication, topics & history
│   │   └── vector_store.py    # ChromaDB persistent collection wrapper
│   ├── cli.py                 # Interactive Command-Line Interface
│   ├── config.py              # Application settings & environment loader
│   ├── dependencies.py        # FastAPI dependency injection singletons
│   └── main.py                # FastAPI app initialization, CORS, lifespan, /ui mounting
├── evals/
│   ├── dataset.py             # Benchmark documents & evaluation questions
│   ├── metrics.py             # Hit Rate@K, Recall@K, and MRR calculations
│   └── run_evaluation.py      # Multi-configuration evaluation benchmark runner
├── tests/
│   ├── conftest.py            # Test client, PDF generator, and isolated temp fixtures
│   ├── test_documents.py      # Document CRUD, deduplication, and validation tests
│   ├── test_evals.py          # Metric mathematical tests
│   ├── test_health.py         # Health check tests
│   ├── test_parser_chunker.py # PyMuPDF & chunking tests
│   ├── test_qa.py             # Q&A, citations, missing evidence, LLM failures
│   └── test_retrieval.py      # Dense, MMR, Hybrid, and filtering tests
├── data/
│   ├── samples/               # Sample PDF, TXT, and Markdown documents
│   └── chroma/                # Persistent vector database (gitignored)
├── Dockerfile                 # Production Docker image definition
├── .dockerignore              # Docker build exclusions
├── .env.example               # Environment variable template
├── .gitignore                 # Git ignore rules
├── PROGRESS.md                # Task implementation log
├── requirements.txt           # Production dependencies
└── render.yaml                # Render cloud deployment blueprint
```

---

## Local Installation

### Prerequisites
- Python 3.11 (recommended) or 3.10+
- Git

### 1. Clone the repository
```bash
git clone https://github.com/sumankr0087/documind-ai.git
cd documind-ai
```

### 2. Create and activate a virtual environment
```bash
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
cp .env.example .env
```
Edit `.env` and set your desired LLM configuration (or leave `LLM_PROVIDER=mock` for testing without API keys).

### 5. Start the development server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Open your browser:
- **Web UI:** `http://localhost:8000/ui`
- **Interactive OpenAPI Documentation:** `http://localhost:8000/docs`

---

## Command-Line Interface (CLI)

DocuMind AI provides a full-featured CLI for managing documents and asking questions directly from your terminal:

```bash
# List all indexed documents
python -m app.cli list

# Upload one or more documents (automatic duplicate skip)
python -m app.cli upload data/samples/architecture_guide.pdf data/samples/overview.md

# Ask a question across all documents
python -m app.cli ask "What tools does DocuMind AI use for vector embeddings?"

# Ask with Hybrid Search (BM25 + Dense) and Cross-Encoder Reranking
python -m app.cli ask "How does sliding overlap prevent context fragmentation?" --hybrid --rerank

# Filter retrieval by file extension
python -m app.cli ask "Explain containerization" --extension pdf

# Scope question to specific document IDs
python -m app.cli ask "What is ChromaDB?" --doc-ids <document_id>

# Start an interactive multi-turn terminal chat session
python -m app.cli chat --topic "Architecture Discussion"

# Run the retrieval evaluation benchmark
python -m app.cli eval
```

---

## Environment Variables

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `HOST` | `0.0.0.0` | Server bind IP address |
| `PORT` | `8000` | Server bind port |
| `APP_ENV` | `development` | Deployment environment (`development`, `production`, `testing`) |
| `CHROMA_PERSIST_DIRECTORY` | `./data/chroma` | Directory where ChromaDB indexes are persisted |
| `CHROMA_COLLECTION_NAME` | `documind_collection` | ChromaDB collection name |
| `SQLITE_DB_PATH` | `./data/documind.db` | SQLite database file for deduplication hashes and chat topics |
| `UPLOAD_DIR` | `./data/uploads` | Local directory for raw file copies |
| `MAX_UPLOAD_SIZE_MB` | `25` | Maximum allowed file upload size in megabytes |
| `EMBEDDING_MODEL_NAME` | `sentence-transformers/all-MiniLM-L6-v2` | Hugging Face model identifier for embeddings |
| `EMBEDDING_DEVICE` | `cpu` | Device for embedding inference (`cpu`, `cuda`, `mps`) |
| `CHUNK_SIZE` | `500` | Character chunk length |
| `CHUNK_OVERLAP` | `100` | Character overlap between consecutive chunks |
| `TOP_K` | `5` | Default number of relevant chunks to retrieve |
| `ENABLE_MMR` | `false` | Enable Maximal Marginal Relevance diversity |
| `MMR_LAMBDA` | `0.7` | Trade-off parameter between query relevance and diversity |
| `ENABLE_HYBRID_SEARCH` | `false` | Enable BM25 keyword + dense vector hybrid search |
| `HYBRID_DENSE_WEIGHT` | `0.6` | Weight assigned to dense vector ranking in RRF |
| `HYBRID_BM25_WEIGHT` | `0.4` | Weight assigned to BM25 keyword ranking in RRF |
| `ENABLE_RERANKING` | `false` | Enable Cross-Encoder passage reranking |
| `RERANKER_MODEL_NAME` | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Model identifier for cross-encoder reranking |
| `LLM_PROVIDER` | `openai` | LLM backend: `openai`, `groq`, `ollama`, or `mock` |
| `OPENAI_API_KEY` | *(empty)* | API key for OpenAI or OpenAI-compatible service |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | Base API endpoint URL |
| `LLM_MODEL` | `gpt-4o-mini` | Model name (e.g. `gpt-4o-mini`, `llama-3.3-70b-versatile`) |
| `LLM_TEMPERATURE` | `0.0` | Sampling temperature for factual consistency |

---

## API Endpoints and Examples

Interactive Swagger documentation is available at `/docs` and ReDoc at `/redoc`.

### 1. Health Check: `GET /health`
```bash
curl http://localhost:8000/health
```

### 2. Batch Upload Documents: `POST /documents/upload-batch`
```bash
curl -X POST http://localhost:8000/documents/upload-batch \
  -F "files=@data/samples/documind_overview.md" \
  -F "files=@data/samples/sample_report.pdf"
```
*Duplicate files are automatically recognized by SHA-256 hash and skipped.*

### 3. Ask a Question with Real-Time Streaming: `POST /questions/ask-stream`
```bash
curl -N -X POST http://localhost:8000/questions/ask-stream \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is ChromaDB used for?",
    "enable_hybrid": true,
    "enable_reranking": true
  }'
```
*Streams Server-Sent Events (`data: {"type": "token", "delta": "..."}`) ending with evidence citations.*

### 4. Chat Topic Sessions: `/chat/sessions`
```bash
# Create a new topic
curl -X POST http://localhost:8000/chat/sessions \
  -H "Content-Type: application/json" \
  -d '{"title": "Research Discussion"}'

# List topics
curl http://localhost:8000/chat/sessions
```

---

## Automated Tests

Run the full automated test suite:
```bash
pytest -q
```

**Results:** `29 passed, 7 warnings in 7.7s`
The test suite covers:
- System health and environment reporting (`tests/test_health.py`)
- Batch ingestion, SHA-256 deduplication, and invalid MIME type handling (`tests/test_documents.py`)
- Multi-page PyMuPDF parsing and sliding-window chunk overlap (`tests/test_parser_chunker.py`)
- Dense, MMR, Hybrid BM25 retrieval and document filtering (`tests/test_retrieval.py`)
- Grounded citations, insufficient evidence detection, and LLM failures (`tests/test_qa.py`)
- Mathematical accuracy of Hit Rate@K, Recall@K, and MRR calculations (`tests/test_evals.py`)

---

## Retrieval Evaluation Benchmark

DocuMind AI includes an offline evaluation harness that measures retrieval quality across 4 different retrieval configurations against benchmark questions without requiring paid LLM API keys:

```bash
python -m evals.run_evaluation
```

### Measured Benchmark Results

| Configuration | Hit Rate@K | Recall@K | Mean Reciprocal Rank (MRR) |
| :--- | :---: | :---: | :---: |
| **Config 1: Standard Dense Search (K=5)** | **1.0000 (100.0%)** | **1.0000 (100.0%)** | **1.0000** |
| **Config 2: Semantic MMR Diversity (K=5, $\lambda=0.7$)** | **1.0000 (100.0%)** | **1.0000 (100.0%)** | **1.0000** |
| **Config 3: Hybrid Search (Dense + BM25, K=5)** | **1.0000 (100.0%)** | **1.0000 (100.0%)** | **1.0000** |
| **Config 4: Hybrid + Cross-Encoder Reranker (K=5)** | **1.0000 (100.0%)** | **1.0000 (100.0%)** | **1.0000** |

---

## Docker & Cloud Deployment

### 1. Build and Run via Docker Locally
```bash
docker build -t documind-ai:latest .
docker run -p 7860:7860 documind-ai:latest
```

### 2. Hugging Face Spaces (100% Free, 24/7 Cloud Hosting)
1. Repository is configured for Hugging Face Spaces Docker SDK on port `7860`.
2. Connect or push to your Space: `https://huggingface.co/spaces/Sumankr0087/documind-ai`.
3. All model weights (`all-MiniLM-L6-v2` and `ms-marco-MiniLM-L-6-v2`) and frontend assets are pre-cached in the Docker image for rapid cold-starts.
4. Your Space runs independently 24/7 on Hugging Face servers without requiring any local laptop execution.

---

## Security Considerations

1. **Prompt Injection Defense:** External document excerpts are treated as untrusted data. They are wrapped inside isolated XML delimiters `<source id="..." file="...">...</source>` accompanied by system directives that strictly prohibit role overrides.
2. **Denial-of-Service Defense:** File uploads are validated before loading into memory. Files exceeding `MAX_UPLOAD_SIZE_MB` (default: 25MB) are rejected with HTTP 413.
3. **Non-Root Container Execution:** The production Dockerfile executes under an unprivileged user (`appuser`, UID 10001) to mitigate container breakout vulnerabilities.
4. **Credential Isolation:** API keys and credentials are exclusively consumed via environment variables. Secret files and `.env` are strictly excluded from version control via `.gitignore`.
