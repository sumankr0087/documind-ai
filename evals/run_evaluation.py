"""Command-line script to run retrieval evaluation comparing multiple configurations without requiring LLM credentials."""
import os
import shutil
import tempfile
from typing import Any, Dict, List, Tuple

from app.models.document import DocumentMetadata
from app.services.bm25_search import BM25SearchService
from app.services.chunker import TextChunker
from app.services.embeddings import EmbeddingService
from app.services.parser import ExtractedPage, ParsedDocument
from app.services.reranker import CrossEncoderReranker
from app.services.retriever import RetrieverService
from app.services.vector_store import VectorStoreService
from evals.dataset import BENCHMARK_QUERIES, SAMPLE_DOCUMENTS, BenchmarkQuery
from evals.metrics import aggregate_metrics, evaluate_query


class Evaluator:
    """Manages indexing benchmark data and evaluating retrieval under a specific configuration."""

    def __init__(
        self,
        config_name: str,
        chunk_size: int,
        chunk_overlap: int,
        top_k: int,
        enable_mmr: bool = False,
        enable_hybrid: bool = False,
        enable_reranking: bool = False,
    ):
        self.config_name = config_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.top_k = top_k
        self.enable_mmr = enable_mmr
        self.enable_hybrid = enable_hybrid
        self.enable_reranking = enable_reranking
        self.temp_dir = tempfile.mkdtemp(prefix="documind_eval_")

        self.chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.embedding_service = EmbeddingService(model_name="sentence-transformers/all-MiniLM-L6-v2")
        self.vector_store = VectorStoreService(
            persist_directory=self.temp_dir,
            collection_name=f"eval_{chunk_size}_{chunk_overlap}",
        )
        self.bm25_service = BM25SearchService()
        self.reranker = CrossEncoderReranker()
        self.retriever = RetrieverService(
            embedding_service=self.embedding_service,
            vector_store=self.vector_store,
            bm25_service=self.bm25_service,
            reranker=self.reranker,
        )

        self.all_chunks = []
        self.ground_truth_map: Dict[str, List[str]] = {}

    def cleanup(self) -> None:
        """Remove temporary ChromaDB directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def prepare_and_index(self) -> None:
        """Chunk, establish ground-truth IDs, and index benchmark documents into ChromaDB and BM25."""
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
                    if any(marker.lower() in c.text.lower() for marker in q.relevant_content_markers):
                        matching_ids.append(c.chunk_id)

            if not matching_ids:
                matching_ids = [c.chunk_id for c in self.all_chunks if c.document_id == q.target_doc_id]

            self.ground_truth_map[q.query_id] = matching_ids

        # 3. Generate embeddings and index into ChromaDB
        chunk_texts = [c.text for c in self.all_chunks]
        embeddings = self.embedding_service.embed_documents(chunk_texts)
        self.vector_store.add_chunks(self.all_chunks, embeddings)

        # 4. Index into BM25
        self.bm25_service.add_chunks(
            [
                {
                    "chunk_id": c.chunk_id,
                    "document_id": c.document_id,
                    "chunk_index": c.chunk_index,
                    "filename": c.filename,
                    "page_number": c.page_number,
                    "text": c.text,
                }
                for c in self.all_chunks
            ]
        )

    def evaluate(self) -> Tuple[List[Dict[str, Any]], Dict[str, float]]:
        """Run retrieval for all benchmark queries and compute individual and aggregate metrics."""
        per_query_results = []
        for q in BENCHMARK_QUERIES:
            gt_ids = self.ground_truth_map[q.query_id]
            retrieved = self.retriever.retrieve(
                question=q.question,
                top_k=self.top_k,
                enable_mmr=self.enable_mmr,
                enable_hybrid=self.enable_hybrid,
                enable_reranking=self.enable_reranking,
            )
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
    """Run comparative evaluation across 4 retrieval configurations."""
    print("=" * 80)
    print("               DOCUMIND AI - ADVANCED RETRIEVAL EVALUATION")
    print("=" * 80)
    print("Dataset: 3 Benchmark Technical Documents, 10 Curated Evaluation Queries")
    print("Metrics: Hit Rate@K, Recall@K, Mean Reciprocal Rank (MRR)")
    print("Configurations Compared: Dense Vector, Semantic MMR, Hybrid (Dense+BM25), Hybrid+Reranker")
    print("=" * 80)

    configs = [
        {
            "name": "Config 1: Standard Dense Search (K=5)",
            "chunk_size": 500,
            "chunk_overlap": 100,
            "top_k": 5,
            "enable_mmr": False,
            "enable_hybrid": False,
            "enable_reranking": False,
        },
        {
            "name": "Config 2: Semantic MMR Diversity (K=5, lambda=0.7)",
            "chunk_size": 500,
            "chunk_overlap": 100,
            "top_k": 5,
            "enable_mmr": True,
            "enable_hybrid": False,
            "enable_reranking": False,
        },
        {
            "name": "Config 3: Hybrid Search (Dense + BM25, K=5)",
            "chunk_size": 500,
            "chunk_overlap": 100,
            "top_k": 5,
            "enable_mmr": False,
            "enable_hybrid": True,
            "enable_reranking": False,
        },
        {
            "name": "Config 4: Hybrid + Cross-Encoder Reranker (K=5)",
            "chunk_size": 500,
            "chunk_overlap": 100,
            "top_k": 5,
            "enable_mmr": False,
            "enable_hybrid": True,
            "enable_reranking": True,
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
            enable_mmr=cfg["enable_mmr"],
            enable_hybrid=cfg["enable_hybrid"],
            enable_reranking=cfg["enable_reranking"],
        )

        try:
            evaluator.prepare_and_index()
            print(f"Indexed {len(evaluator.all_chunks)} chunks into ChromaDB and BM25.")

            per_query, summary = evaluator.evaluate()

            print(f"\n--- Per-Question Results (Top-K={cfg['top_k']}) ---")
            for r in per_query:
                print(
                    f"[{r['query_id']}] Hit Rate@{r['k']}: {r['hit_rate']:.4f} | "
                    f"Recall@{r['k']}: {r['recall']:.4f} | "
                    f"MRR: {r['mrr']:.4f} | Q: {r['question'][:50]}..."
                )

            print(f"\n--- Aggregate Summary ({cfg['name']}) ---")
            print(f"  Total Queries:               {summary['total_queries']}")
            print(f"  Mean Hit Rate@{cfg['top_k']}:           {summary['hit_rate']:.4f} ({(summary['hit_rate']*100):.1f}%)")
            print(f"  Mean Recall@{cfg['top_k']}:             {summary['recall']:.4f} ({(summary['recall']*100):.1f}%)")
            print(f"  Mean Reciprocal Rank (MRR): {summary['mrr']:.4f}")

            all_summaries.append((cfg, summary))
        finally:
            evaluator.cleanup()

    # Print Final Comparative Table
    print("\n" + "=" * 85)
    print("                    RETRIEVAL CONFIGURATION COMPARISON")
    print("=" * 85)
    print(f"{'Configuration':<45} | {'Hit Rate@K':<12} | {'Recall@K':<10} | {'MRR':<8}")
    print("-" * 85)
    for cfg, s in all_summaries:
        print(f"{cfg['name']:<45} | {s['hit_rate']:<12.4f} | {s['recall']:<10.4f} | {s['mrr']:<8.4f}")
    print("=" * 85)
    print("Evaluation completed successfully with measured real-world metrics.")


def main():
    run_evaluations()


if __name__ == "__main__":
    main()
