"""Command-line script to run retrieval evaluation comparing multiple configurations without requiring LLM credentials."""
import os
import shutil
import tempfile
from typing import List, Dict, Any, Tuple

from app.services.chunker import TextChunker
from app.services.embeddings import EmbeddingService
from app.services.parser import ParsedDocument, ExtractedPage
from app.services.retriever import RetrieverService
from app.services.vector_store import VectorStoreService
from evals.dataset import SAMPLE_DOCUMENTS, BENCHMARK_QUERIES, BenchmarkQuery
from evals.metrics import evaluate_query, aggregate_metrics


class Evaluator:
    """Manages indexing benchmark data and evaluating retrieval under a specific configuration."""

    def __init__(self, config_name: str, chunk_size: int, chunk_overlap: int, top_k: int):
        self.config_name = config_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.top_k = top_k
        self.temp_dir = tempfile.mkdtemp(prefix="documind_eval_")

        self.chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.embedding_service = EmbeddingService(model_name="sentence-transformers/all-MiniLM-L6-v2")
        self.vector_store = VectorStoreService(
            persist_directory=self.temp_dir,
            collection_name=f"eval_{chunk_size}_{chunk_overlap}",
        )
        self.retriever = RetrieverService(
            embedding_service=self.embedding_service,
            vector_store=self.vector_store,
        )

        self.all_chunks = []
        self.ground_truth_map: Dict[str, List[str]] = {}

    def cleanup(self) -> None:
        """Remove temporary ChromaDB directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def prepare_and_index(self) -> None:
        """Chunk, establish ground-truth IDs, and index benchmark documents."""
        # 1. Chunk all sample documents
        for doc in SAMPLE_DOCUMENTS:
            parsed_doc = ParsedDocument(
                filename=doc.filename,
                content_type="text/markdown",
                pages=[ExtractedPage(page_number=1, text=doc.content, char_count=len(doc.content))],
                total_chars=len(doc.content),
            )
            chunks = self.chunker.chunk_document(doc.doc_id, parsed_doc)
            self.all_chunks.extend(chunks)

            # Record in vector store registry
            from app.models.document import DocumentMetadata
            meta = DocumentMetadata(
                document_id=doc.doc_id,
                filename=doc.filename,
                content_type="text/markdown",
                size_bytes=len(doc.content),
                chunk_count=len(chunks),
                page_count=1,
            )
            self.vector_store.registry.register_document(meta)

        # 2. Determine ground truth chunk IDs for each query based on content markers
        for q in BENCHMARK_QUERIES:
            matching_ids = []
            for c in self.all_chunks:
                if c.document_id == q.target_doc_id:
                    # Check if any marker is in this chunk text
                    if any(marker.lower() in c.text.lower() for marker in q.relevant_content_markers):
                        matching_ids.append(c.chunk_id)

            # Fallback to all chunks of the target doc if marker was too narrow
            if not matching_ids:
                matching_ids = [c.chunk_id for c in self.all_chunks if c.document_id == q.target_doc_id]

            self.ground_truth_map[q.query_id] = matching_ids

        # 3. Generate embeddings and index
        chunk_texts = [c.text for c in self.all_chunks]
        embeddings = self.embedding_service.embed_documents(chunk_texts)
        self.vector_store.add_chunks(self.all_chunks, embeddings)

    def evaluate(self) -> Tuple[List[Dict[str, Any]], Dict[str, float]]:
        """Run retrieval for all benchmark queries and compute individual and aggregate metrics."""
        per_query_results = []
        for q in BENCHMARK_QUERIES:
            gt_ids = self.ground_truth_map[q.query_id]
            retrieved = self.retriever.retrieve(question=q.question, top_k=self.top_k)
            retrieved_ids = [c.chunk_id for c in retrieved]

            eval_res = evaluate_query(
                query_id=q.query_id,
                question=q.question,
                retrieved_ids=retrieved_ids,
                ground_truth_ids=gt_ids,
                k=self.top_k,
            )
            per_query_results.append(eval_res)

        summary = aggregate_metrics(per_query_results)
        return per_query_results, summary


def run_evaluations():
    """Run comparative evaluation of two retrieval configurations."""
    print("=" * 80)
    print("               DOCUMIND AI - RETRIEVAL EVALUATION HARNESS")
    print("=" * 80)
    print("Dataset: 3 Benchmark Technical Documents, 10 Curated Evaluation Queries")
    print("Metrics: Hit Rate@K, Recall@K, Mean Reciprocal Rank (MRR)")
    print("Note: Running locally without requiring external paid LLM credentials.")
    print("=" * 80)

    configs = [
        {
            "name": "Configuration A (Compact Chunks: Size=350, Overlap=70, Top-K=3)",
            "chunk_size": 350,
            "chunk_overlap": 70,
            "top_k": 3,
        },
        {
            "name": "Configuration B (Standard Chunks: Size=500, Overlap=100, Top-K=5)",
            "chunk_size": 500,
            "chunk_overlap": 100,
            "top_k": 5,
        },
    ]

    all_summaries = []

    for cfg in configs:
        print(f"\n>>> Running Evaluation: {cfg['name']}")
        print("-" * 80)
        evaluator = Evaluator(
            config_name=cfg["name"],
            chunk_size=cfg["chunk_size"],
            chunk_overlap=cfg["chunk_overlap"],
            top_k=cfg["top_k"],
        )

        try:
            evaluator.prepare_and_index()
            print(f"Indexed {len(evaluator.all_chunks)} chunks into isolated ChromaDB collection.")

            per_query, summary = evaluator.evaluate()

            print(f"\n--- Per-Question Results (Top-K={cfg['top_k']}) ---")
            for r in per_query:
                print(f"[{r['query_id']}] Question: {r['question']}")
                print(f"     Ground Truth: {r['ground_truth_ids']}")
                print(f"     Retrieved:    {r['retrieved_ids']}")
                print(
                    f"     Hit Rate@{r['k']}: {r['hit_rate']:.4f} | "
                    f"Recall@{r['k']}: {r['recall']:.4f} | "
                    f"MRR: {r['mrr']:.4f}"
                )

            print(f"\n--- Aggregate Summary ({cfg['name']}) ---")
            print(f"  Total Queries:     {summary['total_queries']}")
            print(f"  Mean Hit Rate@{cfg['top_k']}: {summary['hit_rate']:.4f} ({(summary['hit_rate']*100):.1f}%)")
            print(f"  Mean Recall@{cfg['top_k']}:   {summary['recall']:.4f} ({(summary['recall']*100):.1f}%)")
            print(f"  Mean Reciprocal Rank (MRR): {summary['mrr']:.4f}")

            all_summaries.append((cfg, summary))
        finally:
            evaluator.cleanup()

    # Print Final Comparative Table
    print("\n" + "=" * 80)
    print("                    RETRIEVAL CONFIGURATION COMPARISON")
    print("=" * 80)
    print(f"{'Configuration':<42} | {'Hit Rate@K':<12} | {'Recall@K':<10} | {'MRR':<8}")
    print("-" * 80)
    for cfg, s in all_summaries:
        short_name = f"Chunk={cfg['chunk_size']}, Ovlp={cfg['chunk_overlap']}, K={cfg['top_k']}"
        print(f"{short_name:<42} | {s['hit_rate']:<12.4f} | {s['recall']:<10.4f} | {s['mrr']:<8.4f}")
    print("=" * 80)
    print("Evaluation completed successfully with measured real-world metrics.")


if __name__ == "__main__":
    run_evaluations()
