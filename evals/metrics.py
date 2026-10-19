"""Retrieval evaluation metrics: Hit Rate@K, Recall@K, and Mean Reciprocal Rank (MRR)."""
from typing import List, Dict, Any


def compute_hit_rate_at_k(retrieved_ids: List[str], ground_truth_ids: List[str], k: int) -> float:
    """Compute Hit Rate@K (1.0 if at least one ground truth ID is in top-K, else 0.0)."""
    if not ground_truth_ids:
        return 0.0

    top_k_retrieved = set(retrieved_ids[:k])
    gt_set = set(ground_truth_ids)
    return 1.0 if len(top_k_retrieved.intersection(gt_set)) > 0 else 0.0


def compute_recall_at_k(retrieved_ids: List[str], ground_truth_ids: List[str], k: int) -> float:
    """Compute Recall@K (fraction of ground truth items captured in top-K)."""
    if not ground_truth_ids:
        return 0.0

    top_k_retrieved = set(retrieved_ids[:k])
    gt_set = set(ground_truth_ids)
    hits = len(top_k_retrieved.intersection(gt_set))
    return hits / len(gt_set)


def compute_mrr_at_k(retrieved_ids: List[str], ground_truth_ids: List[str], k: int) -> float:
    """Compute Reciprocal Rank at K (1 / rank of first relevant retrieved item, or 0.0)."""
    if not ground_truth_ids:
        return 0.0

    gt_set = set(ground_truth_ids)
    for rank_idx, chunk_id in enumerate(retrieved_ids[:k], start=1):
        if chunk_id in gt_set:
            return 1.0 / rank_idx
    return 0.0


def evaluate_query(
    query_id: str,
    question: str,
    retrieved_ids: List[str],
    ground_truth_ids: List[str],
    k: int = 5,
) -> Dict[str, Any]:
    """Evaluate a single query and return individual metrics."""
    hit_rate = compute_hit_rate_at_k(retrieved_ids, ground_truth_ids, k)
    recall = compute_recall_at_k(retrieved_ids, ground_truth_ids, k)
    mrr = compute_mrr_at_k(retrieved_ids, ground_truth_ids, k)

    return {
        "query_id": query_id,
        "question": question,
        "k": k,
        "ground_truth_ids": ground_truth_ids,
        "retrieved_ids": retrieved_ids[:k],
        "hit_rate": hit_rate,
        "recall": recall,
        "mrr": mrr,
    }


def aggregate_metrics(query_evaluations: List[Dict[str, Any]]) -> Dict[str, float]:
    """Aggregate per-query evaluations into mean Hit Rate@K, Recall@K, and MRR."""
    if not query_evaluations:
        return {"hit_rate": 0.0, "recall": 0.0, "mrr": 0.0, "total_queries": 0}

    total = len(query_evaluations)
    avg_hit_rate = sum(q["hit_rate"] for q in query_evaluations) / total
    avg_recall = sum(q["recall"] for q in query_evaluations) / total
    avg_mrr = sum(q["mrr"] for q in query_evaluations) / total

    return {
        "total_queries": total,
        "hit_rate": round(avg_hit_rate, 4),
        "recall": round(avg_recall, 4),
        "mrr": round(avg_mrr, 4),
    }
