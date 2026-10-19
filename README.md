# DocuMind AI - Intelligent Document RAG Engine

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

DocuMind AI is a production-grade **Retrieval-Augmented Generation (RAG)** platform designed for high-accuracy document Question & Answering. It integrates high-speed document extraction (PyMuPDF for PDF, plus TXT and Markdown), overlapping semantic chunking, dense vector representations via Sentence Transformers, persistent vector indexing with ChromaDB, and grounded LLM synthesis featuring strict source citations (filename, page numbers, and chunk IDs) and prompt injection defense.

---

## Architecture Overview

```
                   ┌──────────────────────────────────────┐
                   │          User / Client App           │
                   └──────────────────┬───────────────────┘
                                      │
                         HTTP REST API Requests
                                      │
                                      ▼
               ┌──────────────────────────────────────────────┐
               │         FastAPI Web Application (app)        │
               │  - /health                                   │
               │  - /documents/upload, /documents, /{id}      │
               │  - /questions/ask                            │
               └──────────┬────────────────────────┬──────────┘
                          │                        │
       Ingestion Pipeline │                        │ Query & Retrieval Pipeline
                          ▼                        ▼
               ┌─────────────────────┐   ┌─────────────────────┐
               │   DocumentParser    │   │  RetrieverService   │
               │  - PyMuPDF (PDF)    │   │  - Top-5 retrieval  │
               │  - Plain Text & MD  │   │  - Doc ID filtering │
               └──────────┬──────────┘   └──────────┬──────────┘
                          ▼                         ▲
               ┌─────────────────────┐              │ Cosine Distance
               │     TextChunker     │              │ Search
               │  - Overlapping text │              │
               │  - Page tracking    │              │
               └──────────┬──────────┘              │
                          ▼                         ▼
        ┌─────────────────────────────────────────────────────────┐
        │            Embedding & Vector Storage Layer             │
        │  - Sentence Transformers (all-MiniLM-L6-v2)             │
        │  - ChromaDB Persistent HNSW Index                       │
        │  - Document Metadata Registry                           │
        └─────────────────────────┬───────────────────────────────┘
                                  │ Grounded Context
                                  ▼
               ┌──────────────────────────────────────────────┐
               │                  LLMService                  │
               │  - Grounded prompt formulation               │
               │  - Prompt injection isolation (XML delimiters│
               │  - Evidence sufficiency validation           │
               │  - Configurable: OpenAI / Groq / Ollama / Mock│
               └──────────────────┬───────────────────────────┘
                                  │
                                  ▼
                     Structured Answer + Citations
               (Filename, Page Number, Chunk ID, Snippet)
```

---

## Technology Stack

- **API Framework:** FastAPI, Uvicorn (ASGI)
- **Document Parsing:** PyMuPDF (`fitz` / `pymupdf`) for native multi-page PDF text extraction
- **Vector Storage:** ChromaDB with persistent HNSW index and cosine similarity
- **Embedding Model:** Sentence Transformers (`sentence-transformers/all-MiniLM-L6-v2`, 384 dimensions)
- **LLM Integration:** Configurable via OpenAI-compatible API (OpenAI GPT-4o-mini, Groq, Together, Ollama) and offline extractive fallback
- **Validation & Serialization:** Pydantic v2 & Pydantic-Settings
- **Automated Testing:** Pytest, pytest-asyncio, HTTPX
- **Containerization & Deployment:** Docker, Render, Fly.io

---

## Directory Structure

```
documind-ai/
├── app/
│   ├── api/
│   │   ├── documents.py       # Document upload, listing, detail, and deletion
│   │   ├── health.py          # GET /health endpoint
│   │   └── questions.py       # POST /questions/ask RAG endpoint
│   ├── models/
│   │   ├── document.py        # Document & chunk Pydantic schemas
│   │   ├── health.py          # Health check schema
│   │   └── question.py        # Question request/response schemas & Citation
│   ├── services/
│   │   ├── chunker.py         # Overlapping text chunker
│   │   ├── embeddings.py      # Sentence Transformers embedding service
│   │   ├── llm.py             # Configurable LLM & prompt defense service
│   │   ├── parser.py          # PyMuPDF, TXT, and Markdown parser
│   │   ├── retriever.py       # Top-K retrieval & document filtering
│   │   └── vector_store.py    # ChromaDB wrapper & document registry
│   ├── config.py              # Application settings & environment loader
│   ├── dependencies.py        # FastAPI dependency injection singletons
│   └── main.py                # FastAPI app initialization, CORS, lifespan
├── evals/
│   ├── dataset.py             # Benchmark documents & evaluation questions
│   ├── metrics.py             # Hit Rate@K, Recall@K, and MRR calculations
│   └── run_evaluation.py      # python -m evals.run_evaluation runner
├── tests/
│   ├── conftest.py            # Test client, PDF generator, and fixtures
│   ├── test_documents.py      # Document CRUD and validation tests
│   ├── test_evals.py          # Metric mathematical tests
│   ├── test_health.py         # Health check tests
│   ├── test_parser_chunker.py # PyMuPDF & chunking tests
│   ├── test_qa.py             # Q&A, citations, missing evidence, LLM failures
│   └── test_retrieval.py      # Top-K retrieval and document filtering tests
├── data/
│   ├── samples/               # Ready-to-use sample documents
│   └── chroma/                # Persistent vector database (gitignored)
├── Dockerfile                 # Production Docker image definition
├── .dockerignore              # Docker build exclusions
├── .env.example               # Environment variable template
├── .gitignore                 # Git ignore rules
├── PROGRESS.md                # Task implementation log
├── requirements.txt           # Production dependencies
├── render.yaml                # Render cloud deployment blueprint
└── fly.toml                   # Fly.io cloud deployment configuration
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
Open your browser at `http://localhost:8000/docs` to view the interactive OpenAPI documentation.

---

## Environment Variables

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `HOST` | `0.0.0.0` | Server bind IP address |
| `PORT` | `8000` | Server bind port |
| `APP_ENV` | `development` | Deployment environment (`development`, `production`, `testing`) |
| `CHROMA_PERSIST_DIRECTORY` | `./data/chroma` | Directory where ChromaDB indexes are persisted |
| `CHROMA_COLLECTION_NAME` | `documind_collection` | ChromaDB collection name |
| `UPLOAD_DIR` | `./data/uploads` | Local directory for raw file copies |
| `MAX_UPLOAD_SIZE_MB` | `25` | Maximum allowed file upload size in megabytes |
| `EMBEDDING_MODEL_NAME` | `sentence-transformers/all-MiniLM-L6-v2` | Hugging Face model identifier for embeddings |
| `EMBEDDING_DEVICE` | `cpu` | Device for embedding inference (`cpu`, `cuda`, `mps`) |
| `CHUNK_SIZE` | `500` | Character chunk length |
| `CHUNK_OVERLAP` | `100` | Character overlap between consecutive chunks |
| `TOP_K` | `5` | Default number of relevant chunks to retrieve |
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
curl -X GET http://localhost:8000/health
```
**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "app_env": "development",
  "services": {
    "vector_store": {
      "status": "connected",
      "collection": "documind_collection",
      "total_chunks": 12
    },
    "embedding": {
      "model": "sentence-transformers/all-MiniLM-L6-v2",
      "device": "cpu"
    },
    "llm": {
      "provider": "openai",
      "model": "gpt-4o-mini",
      "configured": true
    }
  }
}
```

### 2. Ingest Document: `POST /documents/upload`
Supports PDF (`.pdf`), plain text (`.txt`), and Markdown (`.md`).
```bash
curl -X POST http://localhost:8000/documents/upload \
  -F "file=@data/samples/documind_overview.md"
```
**Response:**
```json
{
  "message": "Document 'documind_overview.md' successfully ingested and indexed.",
  "document": {
    "document_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "filename": "documind_overview.md",
    "content_type": "text/markdown",
    "size_bytes": 894,
    "chunk_count": 2,
    "page_count": null,
    "created_at": "2026-10-20T00:15:00.000000"
  }
}
```

### 3. List Ingested Documents: `GET /documents`
```bash
curl -X GET http://localhost:8000/documents
```

### 4. Get Document Details: `GET /documents/{document_id}`
```bash
curl -X GET http://localhost:8000/documents/9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d
```

### 5. Ask Grounded Question: `POST /questions/ask`
```bash
curl -X POST http://localhost:8000/questions/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What tools does DocuMind AI use for PDF extraction and embeddings?",
    "document_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "top_k": 3
  }'
```
**Response:**
```json
{
  "question": "What tools does DocuMind AI use for PDF extraction and embeddings?",
  "answer": "DocuMind AI uses PyMuPDF for high-speed PDF text extraction and Sentence Transformers (all-MiniLM-L6-v2) to generate normalized 384-dimensional dense vector embeddings.",
  "citations": [
    {
      "chunk_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d_chunk_0",
      "document_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "filename": "documind_overview.md",
      "page_number": null,
      "snippet": "Multi-Format Ingestion: Accepts PDF documents (via PyMuPDF)... Sentence Transformers (all-MiniLM-L6-v2)...",
      "relevance_score": 0.8845
    }
  ],
  "evidence_sufficient": true,
  "document_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "model_used": "gpt-4o-mini"
}
```

### 6. Delete Document: `DELETE /documents/{document_id}`
```bash
curl -X DELETE http://localhost:8000/documents/9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d
```

---

## Automated Tests

Run the full automated test suite:
```bash
pytest -q
```

The test suite covers:
- System health and environment reporting (`tests/test_health.py`)
- Document ingestion, oversized file rejections, and invalid MIME type handling (`tests/test_documents.py`)
- Multi-page PyMuPDF parsing, character offsets, and chunk overlap mechanics (`tests/test_parser_chunker.py`)
- Semantic similarity retrieval and document ID scoping (`tests/test_retrieval.py`)
- Source citations, missing evidence detection, and upstream LLM failure modes (`tests/test_qa.py`)
- Mathematical accuracy of Hit Rate@K, Recall@K, and MRR calculations (`tests/test_evals.py`)

---

## Retrieval Evaluation

DocuMind AI includes an offline retrieval evaluation harness that measures retrieval quality against benchmark datasets without requiring paid LLM API keys.

Run the evaluation:
```bash
python -m evals.run_evaluation
```

### Measured Benchmark Results

| Metric | Configuration A (Compact: Size=350, Ovlp=70, K=3) | Configuration B (Standard: Size=500, Ovlp=100, K=5) |
| :--- | :--- | :--- |
| **Total Test Queries** | 10 | 10 |
| **Hit Rate@K** | **1.0000 (100%)** | **1.0000 (100%)** |
| **Recall@K** | **1.0000 (100%)** | **1.0000 (100%)** |
| **Mean Reciprocal Rank (MRR)** | **1.0000** | **1.0000** |

---

## Docker Containerization

### 1. Build the Docker image
```bash
docker build -t documind-ai:latest .
```

### 2. Run the container
```bash
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/data/chroma:/app/data/chroma \
  -e PORT=8000 \
  -e OPENAI_API_KEY="your-api-key" \
  --name documind \
  documind-ai:latest
```

Verify container status:
```bash
curl http://localhost:8000/health
```

---

## Public Cloud Deployment

DocuMind AI is configured for one-click deployment to public cloud providers that support Docker and persistent volumes.

### Option A: Render (Recommended)
1. Fork or push this repository to GitHub (`https://github.com/sumankr0087/documind-ai`).
2. Log into [Render Dashboard](https://dashboard.render.com).
3. Click **New +** -> **Blueprint**.
4. Connect the repository `documind-ai`. Render will automatically detect `render.yaml`.
5. Set `OPENAI_API_KEY` under Environment Variables.
6. Click **Apply**. The persistent disk `/app/data` ensures your indexed documents and ChromaDB data persist across restarts.

### Option B: Fly.io
1. Install Fly CLI: `brew install flyctl`
2. Authenticate: `fly auth login`
3. Launch app: `fly launch`
4. Create persistent volume:
   ```bash
   fly volumes create documind_data --size 10 --region iad
   ```
5. Deploy:
   ```bash
   fly deploy
   ```

---

## Security Considerations

1. **Prompt Injection Defense:** External document excerpts are treated as untrusted data. They are wrapped inside isolated XML delimiters `<source id="..." file="...">...</source>` accompanied by system directives that strictly prohibit role overrides.
2. **Denial-of-Service Defense:** File uploads are validated before loading into memory. Files exceeding `MAX_UPLOAD_SIZE_MB` (default: 25MB) are rejected with HTTP 413.
3. **Non-Root Container Execution:** The production Dockerfile creates and executes under an unprivileged user (`appuser`, UID 10001) to mitigate container breakout vulnerabilities.
4. **Credential Isolation:** API keys and credentials are exclusively consumed via environment variables. Secret files and `.env` are strictly excluded from version control via `.gitignore`.
