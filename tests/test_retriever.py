"""Tests for core/recommendation/retriever.py

Strategy:
- retrieve() only returns schemes in candidate_ids
- retrieve() respects k limit
- retrieve() returns empty list for empty candidate_ids
- match_score is between 0 and 1
- results are ordered best-first (descending score)
- retrieve() with k > candidates returns at most len(candidates) results

Note: These tests require the index to be built first.
Run: python -m scripts.build_index
"""

import pytest

from core.recommendation.retriever import SchemeRetriever

# Load retriever once for the whole test session (model load is slow)
@pytest.fixture(scope="module")
def retriever():
    return SchemeRetriever()


@pytest.fixture(scope="module")
def all_ids(retriever):
    """All scheme_ids in the index."""
    results = retriever._collection.get()
    return results["ids"]


def test_retriever_loads(retriever):
    """Retriever initialises and collection has documents."""
    assert retriever._collection.count() == 36


def test_retrieve_respects_candidate_ids(retriever, all_ids):
    """retrieve() must never return a scheme not in candidate_ids."""
    subset = all_ids[:5]
    matches = retriever.retrieve("collateral-free loan for small business", subset, k=10)
    returned_ids = {m.scheme.scheme_id for m in matches}
    assert returned_ids.issubset(set(subset))


def test_retrieve_respects_k(retriever, all_ids):
    """retrieve() returns at most k results."""
    matches = retriever.retrieve("working capital loan", all_ids, k=3)
    assert len(matches) <= 3


def test_retrieve_empty_candidates_returns_empty(retriever):
    """retrieve() with empty candidate_ids returns [] immediately."""
    matches = retriever.retrieve("any query", [], k=5)
    assert matches == []


def test_match_scores_between_0_and_1(retriever, all_ids):
    """All match scores must be in [0, 1]."""
    matches = retriever.retrieve("term loan for manufacturing", all_ids, k=5)
    for m in matches:
        assert 0.0 <= m.match_score <= 1.0, f"Score out of range: {m.match_score}"


def test_results_ordered_descending(retriever, all_ids):
    """Results must be ordered best-first (highest score first)."""
    matches = retriever.retrieve("mudra loan for micro enterprise", all_ids, k=10)
    scores = [m.match_score for m in matches]
    assert scores == sorted(scores, reverse=True)


def test_retrieve_k_larger_than_candidates(retriever):
    """k > len(candidates) should return at most len(candidates) results."""
    small_subset = ["cgtmse", "pmmy_mudra"]
    matches = retriever.retrieve("small business loan", small_subset, k=10)
    assert len(matches) <= 2


def test_retrieve_returns_scheme_documents(retriever, all_ids):
    """Each match must have a fully populated SchemeDocument."""
    matches = retriever.retrieve("women entrepreneur loan", all_ids, k=3)
    for m in matches:
        assert m.scheme.scheme_id
        assert m.scheme.name
        assert m.scheme.retrieval_text
        assert m.eligibility_explanation == ""  # filled by ranker