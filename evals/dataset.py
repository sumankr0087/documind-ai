"""Evaluation dataset containing sample documents, benchmark questions, and ground-truth targets."""
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class BenchmarkDocument:
    doc_id: str
    filename: str
    content: str


@dataclass
class BenchmarkQuery:
    query_id: str
    question: str
    target_doc_id: str
    # Keywords or topic markers that identify the relevant ground truth chunk
    relevant_content_markers: List[str]


SAMPLE_DOCUMENTS: List[BenchmarkDocument] = [
    BenchmarkDocument(
        doc_id="eval_doc_rag",
        filename="rag_architecture_guide.md",
        content="""# Retrieval-Augmented Generation Architecture

Retrieval-Augmented Generation (RAG) is a pattern that augments Large Language Models with external domain knowledge.
By separating document retrieval from response generation, RAG mitigates hallucinations and enables real-time information grounding.

Vector embeddings convert unstructured text into dense numerical representations where semantic similarity corresponds to geometric proximity.
Sentence Transformers produce embeddings using pre-trained transformer encoders fine-tuned with contrastive learning objectives.
Cosine similarity is the preferred distance metric because it normalizes for varying vector lengths across sentences.

Chunking strategies dictate retrieval precision and context continuity.
Fixed-size character chunking with sliding overlap ensures that boundary sentences are not split arbitrarily.
Overlapping windows typically retain between 10% and 25% of adjacent text to preserve co-references and semantic links.
Smaller chunk sizes improve retrieval granularity but risk fragmenting complete thoughts, while larger chunk sizes provide rich context at the cost of lower precision.

ChromaDB operates as an embedded vector database supporting persistent HNSW indexing and metadata filtering.
Collection queries return nearest neighbors alongside cosine distances and custom payload attributes such as document identifiers and page indices.
""",
    ),
    BenchmarkDocument(
        doc_id="eval_doc_devops",
        filename="cloud_native_devops.md",
        content="""# Cloud Native Deployment and Containerization

Modern microservices follow twelve-factor application methodology for portability and continuous delivery.
Applications store configuration strictly in environment variables rather than hardcoded application code or checked-in repository files.
The PORT environment variable allows dynamic binding across platforms like Render, Fly.io, and Kubernetes.

Docker containerization packages application source code, runtime dependencies, and system libraries into an immutable artifact.
Multi-stage Docker builds reduce container image footprints and eliminate build toolchains from production images.
Non-root system users minimize security risks inside containers by restricting privilege escalation vulnerabilities.

Health check endpoints expose internal service availability and dependency readiness for load balancers.
The HTTP GET /health endpoint verifies database connectivity, disk availability, and model initialization before traffic routing begins.
Graceful shutdown signals allow active HTTP requests to complete before process termination.
""",
    ),
    BenchmarkDocument(
        doc_id="eval_doc_security",
        filename="llm_security_and_trust.md",
        content="""# LLM Security and Prompt Injection Defense

Prompt injection occurs when untrusted user inputs manipulate the system instructions or control flow of a language model.
Direct prompt injections alter system behavior through explicit instruction overrides such as 'ignore previous instructions'.
Indirect prompt injections arise when documents ingested during RAG contain adversarial commands designed to mislead the model.

Defensive system prompting creates strict semantic boundaries between instructions and untrusted document excerpts.
Context delimiters such as XML tags isolate external documents from core directives, instructing models to treat documents as data rather than instructions.
Input sanitization removes non-printable control characters and dangerous escape sequences prior to prompt construction.

Grounded answering requires models to reject queries where evidence is lacking rather than fabricating convincing answers.
When retrieved chunks fail to supply sufficient verification, the system issues a standardized insufficient evidence notice.
Source citations map generated assertions back to specific document filenames, page numbers, and chunk identifiers for human auditing.
""",
    ),
]


BENCHMARK_QUERIES: List[BenchmarkQuery] = [
    BenchmarkQuery(
        query_id="q1",
        question="What is the role of cosine similarity in vector embeddings?",
        target_doc_id="eval_doc_rag",
        relevant_content_markers=["Cosine similarity is the preferred distance metric", "geometric proximity"],
    ),
    BenchmarkQuery(
        query_id="q2",
        question="How does sliding overlap in chunking prevent context loss?",
        target_doc_id="eval_doc_rag",
        relevant_content_markers=["sliding overlap", "boundary sentences", "preserve co-references"],
    ),
    BenchmarkQuery(
        query_id="q3",
        question="How does ChromaDB index and query document embeddings?",
        target_doc_id="eval_doc_rag",
        relevant_content_markers=["ChromaDB operates as an embedded vector database", "HNSW indexing"],
    ),
    BenchmarkQuery(
        query_id="q4",
        question="Why should configuration be stored in environment variables according to twelve-factor principles?",
        target_doc_id="eval_doc_devops",
        relevant_content_markers=["twelve-factor application methodology", "strictly in environment variables"],
    ),
    BenchmarkQuery(
        query_id="q5",
        question="What are the security benefits of using non-root users in Docker containers?",
        target_doc_id="eval_doc_devops",
        relevant_content_markers=["Non-root system users minimize security risks", "privilege escalation"],
    ),
    BenchmarkQuery(
        query_id="q6",
        question="What does the GET /health endpoint verify before routing traffic?",
        target_doc_id="eval_doc_devops",
        relevant_content_markers=["HTTP GET /health endpoint verifies database connectivity"],
    ),
    BenchmarkQuery(
        query_id="q7",
        question="What is the difference between direct and indirect prompt injection?",
        target_doc_id="eval_doc_security",
        relevant_content_markers=["Direct prompt injections", "Indirect prompt injections", "adversarial commands"],
    ),
    BenchmarkQuery(
        query_id="q8",
        question="How do XML delimiters and context boundaries protect against prompt injection?",
        target_doc_id="eval_doc_security",
        relevant_content_markers=["Context delimiters such as XML tags", "isolate external documents"],
    ),
    BenchmarkQuery(
        query_id="q9",
        question="What should a grounded RAG system do when evidence is insufficient?",
        target_doc_id="eval_doc_security",
        relevant_content_markers=["Grounded answering requires models to reject queries", "insufficient evidence notice"],
    ),
    BenchmarkQuery(
        query_id="q10",
        question="What metadata is included in source citations for auditing?",
        target_doc_id="eval_doc_security",
        relevant_content_markers=["Source citations map generated assertions", "filenames, page numbers, and chunk identifiers"],
    ),
]
