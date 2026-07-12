"""Recommendation engine: wires filter → retriever → ranker into one call.

This is the single public entry point for scheme recommendations.
All business logic lives in filter.py, retriever.py, and ranker.py.
"""

import logging
from typing import List

from core.recommendation.filter import ConstraintFilter
from core.recommendation.ranker import HybridRanker
from core.recommendation.retriever import SchemeRetriever
from core.schema import BusinessProfile, RecommendationResult

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Orchestrates the full recommendation pipeline.

    Pipeline:
        1. ConstraintFilter  → hard eligibility, returns List[SchemeDocument]
        2. SchemeRetriever   → semantic ranking, returns List[SchemeMatch]
        3. HybridRanker      → combined score + explanations, returns List[SchemeMatch]

    Heavy objects (model, ChromaDB client) are loaded once on __init__.
    """

    def __init__(self):
        logger.info("Initialising RecommendationEngine…")
        self._filter = ConstraintFilter()
        self._retriever = SchemeRetriever()
        self._ranker = HybridRanker()
        logger.info("RecommendationEngine ready.")

    def recommend(
        self, profile: BusinessProfile, top_k: int = 5
    ) -> RecommendationResult:
        """Run the full pipeline and return top_k ranked scheme matches.

        Args:
            profile: Validated BusinessProfile from the assessment form.
            top_k: Maximum number of schemes to return.

        Returns:
            RecommendationResult with ranked matches and total count.
        """
        # Stage 1: hard eligibility filter
        eligible = self._filter.filter(profile)
        logger.info(
            "[%s] Stage 1 filter: %d eligible schemes",
            profile.business_name, len(eligible),
        )

        if not eligible:
            logger.warning("[%s] No eligible schemes — returning empty result", profile.business_name)
            return RecommendationResult(matches=[], total_found=0)

        # Stage 2: semantic retrieval (query = sector + loan need)
        candidate_ids = [s.scheme_id for s in eligible]
        query = (
            f"{profile.sector} business in {profile.state} seeking "
            f"₹{int(profile.loan_amount_sought_inr):,} loan, "
            f"{'with' if profile.has_collateral else 'without'} collateral, "
            f"{profile.vintage_months} months vintage"
        )
        retrieved = self._retriever.retrieve(query, candidate_ids, k=top_k * 2)
        logger.info(
            "[%s] Stage 2 retrieval: %d candidates returned",
            profile.business_name, len(retrieved),
        )

        # Stage 3: hybrid ranking
        ranked = self._ranker.rank(profile, eligible, retrieved)
        top = ranked[:top_k]

        logger.info(
            "[%s] Stage 3 ranking: returning top %d of %d",
            profile.business_name, len(top), len(ranked),
        )

        return RecommendationResult(matches=top, total_found=len(eligible))