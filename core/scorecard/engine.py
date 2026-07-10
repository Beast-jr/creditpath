"""Scorecard engine: runs all six scorers, applies weights, assigns tier."""

import time
from typing import List

from core.schema import BusinessProfile, DimensionScore, ScorecardResult
from core.schema import validate_business_profile
from core.scorecard import dimensions as d
from core.scorecard.weights import DIMENSION_WEIGHTS

# Tier thresholds on the weighted score (0-100)
TIER_LOAN_READY_MIN = 70.0
TIER_NEARLY_READY_MIN = 50.0
TIER_NEEDS_WORK_MIN = 30.0

WEAKEST_COUNT = 2   # how many weakest dimensions to surface


def _assign_tier(weighted_score: float) -> str:
    """Map a weighted score to a readiness tier."""
    if weighted_score >= TIER_LOAN_READY_MIN:
        return "LOAN_READY"
    if weighted_score >= TIER_NEARLY_READY_MIN:
        return "NEARLY_READY"
    if weighted_score >= TIER_NEEDS_WORK_MIN:
        return "NEEDS_WORK"
    return "NOT_READY"


def score_business(profile: BusinessProfile) -> ScorecardResult:
    """Score a profile across all six dimensions and return a full ScorecardResult."""
    start = time.perf_counter()
    validate_business_profile(profile)   # reject bad input before scoring

    scores: List[DimensionScore] = [
        d.score_cash_flow_consistency(profile),
        d.score_debt_service_coverage(profile),
        d.score_gst_regularity(profile),
        d.score_business_vintage(profile),
        d.score_sectoral_risk(profile),
        d.score_collateral(profile),
    ]

    weighted_score = sum(
        s.score * DIMENSION_WEIGHTS[s.dimension_name] for s in scores
    )

    weakest = [
        s.dimension_name
        for s in sorted(scores, key=lambda s: s.score)[:WEAKEST_COUNT]
    ]

    elapsed_ms = (time.perf_counter() - start) * 1000
    return ScorecardResult(
        dimension_scores=scores,
        weighted_score=round(weighted_score, 2),
        tier=_assign_tier(weighted_score),
        weakest_dimensions=weakest,
        execution_time_ms=round(elapsed_ms, 3),
    )