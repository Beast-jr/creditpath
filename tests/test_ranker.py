"""Tests for core/recommendation/ranker.py and core/recommendation/engine.py"""

import pytest

from core.recommendation.ranker import (
    ELIGIBILITY_WEIGHT,
    SEMANTIC_WEIGHT,
    HybridRanker,
)
from core.schema import BusinessProfile, SchemeDocument, SchemeMatch


# ── Helpers ──────────────────────────────────────────────────────

def _base_profile(**overrides) -> BusinessProfile:
    defaults = dict(
        business_name="Test Co",
        owner_name="Test Owner",
        sector="manufacturing",
        city="Bengaluru",
        state="karnataka",
        geographic_tier=2,
        monthly_revenue_inr=500_000,
        revenue_consistency_pct=80.0,
        existing_emi_inr=10_000,
        gst_filing_rate_pct=90.0,
        vintage_months=36,
        has_collateral=True,
        collateral_value_inr=1_000_000,
        loan_amount_sought_inr=500_000,
    )
    defaults.update(overrides)
    return BusinessProfile(**defaults)


def _base_scheme(**overrides) -> SchemeDocument:
    defaults = dict(
        scheme_id="test_scheme",
        name="Test Scheme",
        administered_by="Test Bank",
        scheme_type="term_loan",
        target_segments=["micro", "small", "manufacturing"],
        loan_range_min=100_000,
        loan_range_max=5_000_000,
        interest_rate_min=8.0,
        interest_rate_max=12.0,
        collateral_required=False,
        eligibility_vintage_months_min=12,
        eligibility_gst_required=False,
        eligibility_sectors_included=[],
        eligibility_sectors_excluded=[],
        eligibility_geographic_restriction="",
        retrieval_text="A test scheme for unit testing.",
        official_url="https://example.com",
        last_verified_date="2026-07-12",
    )
    defaults.update(overrides)
    return SchemeDocument(**defaults)


def _base_match(scheme=None, score=0.8) -> SchemeMatch:
    return SchemeMatch(
        scheme=scheme or _base_scheme(),
        match_score=score,
        eligibility_explanation="",
    )


# ── Weight constants ─────────────────────────────────────────────

def test_weights_sum_to_one():
    assert abs(SEMANTIC_WEIGHT + ELIGIBILITY_WEIGHT - 1.0) < 1e-9


# ── Eligibility match score ──────────────────────────────────────

def test_eligibility_score_between_0_and_1():
    ranker = HybridRanker()
    score = ranker._compute_eligibility_match_score(_base_profile(), _base_scheme())
    assert 0.0 <= score <= 1.0


def test_eligibility_score_higher_for_better_match():
    ranker = HybridRanker()
    # Strong profile: has collateral, high GST, sector matches, good vintage
    strong = _base_profile(
        sector="manufacturing",
        has_collateral=True,
        gst_filing_rate_pct=90.0,
        vintage_months=48,
        loan_amount_sought_inr=300_000,
    )
    # Weak profile: no collateral, low GST, sector mismatch, low vintage
    weak = _base_profile(
        sector="retail",
        has_collateral=False,
        gst_filing_rate_pct=30.0,
        vintage_months=6,
        loan_amount_sought_inr=4_800_000,
    )
    scheme = _base_scheme(target_segments=["manufacturing"])
    strong_score = ranker._compute_eligibility_match_score(strong, scheme)
    weak_score = ranker._compute_eligibility_match_score(weak, scheme)
    assert strong_score > weak_score


# ── Explanation generation ───────────────────────────────────────

def test_explanation_contains_scheme_name():
    ranker = HybridRanker()
    scheme = _base_scheme(name="CGTMSE Credit Guarantee")
    explanation = ranker._generate_match_explanation(_base_profile(), scheme)
    assert "CGTMSE Credit Guarantee" in explanation


def test_explanation_contains_loan_amount():
    ranker = HybridRanker()
    explanation = ranker._generate_match_explanation(
        _base_profile(loan_amount_sought_inr=500_000), _base_scheme()
    )
    assert "500,000" in explanation


def test_explanation_mentions_no_collateral_required():
    ranker = HybridRanker()
    scheme = _base_scheme(collateral_required=False)
    explanation = ranker._generate_match_explanation(_base_profile(), scheme)
    assert "No collateral" in explanation


def test_explanation_mentions_sector_match():
    ranker = HybridRanker()
    scheme = _base_scheme(target_segments=["manufacturing"])
    explanation = ranker._generate_match_explanation(
        _base_profile(sector="manufacturing"), scheme
    )
    assert "manufacturing" in explanation.lower()


def test_explanation_not_empty():
    ranker = HybridRanker()
    explanation = ranker._generate_match_explanation(_base_profile(), _base_scheme())
    assert len(explanation) > 20


# ── rank() ───────────────────────────────────────────────────────

def test_rank_output_sorted_descending():
    ranker = HybridRanker()
    profile = _base_profile()
    schemes = [_base_scheme(scheme_id=f"s{i}") for i in range(3)]
    retrieved = [
        _base_match(schemes[0], score=0.9),
        _base_match(schemes[1], score=0.5),
        _base_match(schemes[2], score=0.7),
    ]
    result = ranker.rank(profile, schemes, retrieved)
    scores = [m.match_score for m in result]
    assert scores == sorted(scores, reverse=True)


def test_rank_fills_explanation():
    ranker = HybridRanker()
    profile = _base_profile()
    scheme = _base_scheme()
    retrieved = [_base_match(scheme, score=0.8)]
    result = ranker.rank(profile, [scheme], retrieved)
    assert result[0].eligibility_explanation != ""


def test_rank_drops_scheme_not_in_filtered(caplog):
    """Schemes not in filtered_schemes must be silently dropped."""
    ranker = HybridRanker()
    profile = _base_profile()
    filtered = [_base_scheme(scheme_id="allowed")]
    intruder = _base_scheme(scheme_id="intruder")
    retrieved = [_base_match(intruder, score=0.99)]
    result = ranker.rank(profile, filtered, retrieved)
    assert result == []


def test_rank_final_score_uses_formula():
    """final_score = 0.6 * similarity + 0.4 * eligibility_score"""
    ranker = HybridRanker()
    profile = _base_profile()
    scheme = _base_scheme()
    similarity = 0.8
    retrieved = [_base_match(scheme, score=similarity)]
    result = ranker.rank(profile, [scheme], retrieved)
    eligibility = ranker._compute_eligibility_match_score(profile, scheme)
    expected = round(SEMANTIC_WEIGHT * similarity + ELIGIBILITY_WEIGHT * eligibility, 4)
    assert result[0].match_score == expected


def test_rank_empty_retrieved_returns_empty():
    ranker = HybridRanker()
    result = ranker.rank(_base_profile(), [_base_scheme()], [])
    assert result == []


# ── RecommendationEngine integration ─────────────────────────────

def test_engine_returns_recommendation_result():
    from core.recommendation.engine import RecommendationEngine
    from core.schema import RecommendationResult
    engine = RecommendationEngine()
    profile = _base_profile()
    result = engine.recommend(profile, top_k=5)
    assert isinstance(result, RecommendationResult)


def test_engine_returns_at_most_top_k():
    from core.recommendation.engine import RecommendationEngine
    engine = RecommendationEngine()
    result = engine.recommend(_base_profile(), top_k=3)
    assert len(result.matches) <= 3


def test_engine_total_found_gte_matches():
    from core.recommendation.engine import RecommendationEngine
    engine = RecommendationEngine()
    result = engine.recommend(_base_profile(), top_k=3)
    assert result.total_found >= len(result.matches)


def test_engine_all_matches_have_explanations():
    from core.recommendation.engine import RecommendationEngine
    engine = RecommendationEngine()
    result = engine.recommend(_base_profile(), top_k=5)
    for match in result.matches:
        assert len(match.eligibility_explanation) > 0


def test_engine_scores_between_0_and_1():
    from core.recommendation.engine import RecommendationEngine
    engine = RecommendationEngine()
    result = engine.recommend(_base_profile(), top_k=5)
    for match in result.matches:
        assert 0.0 <= match.match_score <= 1.0