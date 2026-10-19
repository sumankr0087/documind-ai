"""Automated tests for evaluation metrics (Hit Rate@K, Recall@K, MRR)."""
from evals.metrics import (
    compute_hit_rate_at_k,
    compute_recall_at_k,
    compute_mrr_at_k,
    evaluate_query,
    aggregate_metrics,
)


def test_hit_rate_at_k():
    """Verify Hit Rate@K computation."""
    retrieved = ["c1", "c2", "c3", "c4", "c5"]

    # When ground truth is in top-k
    assert compute_hit_rate_at_k(retrieved, ["c1"], k=3) == 1.0
    assert compute_hit_rate_at_k(retrieved, ["c3"], k=3) == 1.0

    # When ground truth is outside top-k
    assert compute_hit_rate_at_k(retrieved, ["c4"], k=3) == 0.0

    # When ground truth is empty
    assert compute_hit_rate_at_k(retrieved, [], k=5) == 0.0


def test_recall_at_k():
    """Verify Recall@K computation."""
    retrieved = ["c1", "c2", "c3", "c4", "c5"]

    # All GT captured
    assert compute_recall_at_k(retrieved, ["c1", "c2"], k=3) == 1.0

    # 1 of 2 captured
    assert compute_recall_at_k(retrieved, ["c2", "c6"], k=3) == 0.5

    # None captured
    assert compute_recall_at_k(retrieved, ["c7", "c8"], k=3) == 0.0


def test_mrr_at_k():
    """Verify Mean Reciprocal Rank (MRR) computation."""
    retrieved = ["c1", "c2", "c3", "c4", "c5"]

    # First item matches -> 1 / 1 = 1.0
    assert compute_mrr_at_k(retrieved, ["c1"], k=5) == 1.0

    # Second item matches -> 1 / 2 = 0.5
    assert compute_mrr_at_k(retrieved, ["c2"], k=5) == 0.5

    # Third item matches -> 1 / 3 = 0.3333...
    assert round(compute_mrr_at_k(retrieved, ["c3"], k=5), 4) == 0.3333

    # No item matches in top k
    assert compute_mrr_at_k(retrieved, ["c9"], k=5) == 0.0


def test_evaluate_query_and_aggregation():
    """Verify query evaluation and aggregation across multiple queries."""
    q1 = evaluate_query("q1", "Question 1", ["c1", "c2"], ["c1"], k=2)
    q2 = evaluate_query("q2", "Question 2", ["c3", "c4"], ["c4"], k=2)
    q3 = evaluate_query("q3", "Question 3", ["c5", "c6"], ["c9"], k=2)

    assert q1["hit_rate"] == 1.0
    assert q1["mrr"] == 1.0

    assert q2["hit_rate"] == 1.0
    assert q2["mrr"] == 0.5

    assert q3["hit_rate"] == 0.0
    assert q3["mrr"] == 0.0

    agg = aggregate_metrics([q1, q2, q3])
    assert agg["total_queries"] == 3
    # Hit rate: (1.0 + 1.0 + 0.0) / 3 = 0.6667
    assert agg["hit_rate"] == 0.6667
    # Recall: (1.0 + 1.0 + 0.0) / 3 = 0.6667
    assert agg["recall"] == 0.6667
    # MRR: (1.0 + 0.5 + 0.0) / 3 = 0.5000
    assert agg["mrr"] == 0.5000
