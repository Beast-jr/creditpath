"""Hybrid ranker: combines semantic similarity with eligibility match score.

Ranking formula:
    final_score = SEMANTIC_WEIGHT * similarity + ELIGIBILITY_WEIGHT * eligibility_score

Constants are documented here and nowhere else.
"""

import logging
from typing import List

from core.schema import BusinessProfile, SchemeDocument, SchemeMatch

logger = logging.getLogger(__name__)

# Ranking weights — must sum to 1.0
SEMANTIC_WEIGHT = 0.6     # semantic similarity score from ChromaDB retriever
ELIGIBILITY_WEIGHT = 0.4  # fraction of optional soft criteria met

assert abs(SEMANTIC_WEIGHT + ELIGIBILITY_WEIGHT - 1.0) < 1e-9, "Weights must sum to 1.0"


class HybridRanker:
    """Re-ranks retrieved schemes by combining semantic and eligibility scores.

    The constraint filter guarantees hard eligibility. This ranker adds soft
    scoring: how well does the scheme fit beyond minimum requirements?
    """

    def rank(
        self,
        profile: BusinessProfile,
        filtered_schemes: List[SchemeDocument],
        retrieved: List[SchemeMatch],
    ) -> List[SchemeMatch]:
        """Combine semantic + eligibility scores and return sorted matches.

        Args:
            profile: The business being assessed.
            filtered_schemes: All schemes that passed the constraint filter.
            retrieved: Schemes returned by the retriever with similarity scores.

        Returns:
            SchemeMatch list sorted by final_score descending.
        """
        # Index filtered schemes by id for O(1) lookup
        filtered_ids = {s.scheme_id for s in filtered_schemes}

        # Safety: drop any retrieved scheme that somehow slipped past the filter
        safe = [m for m in retrieved if m.scheme.scheme_id in filtered_ids]
        if len(safe) < len(retrieved):
            logger.warning(
                "Ranker dropped %d scheme(s) not in filtered set",
                len(retrieved) - len(safe),
            )

        ranked = []
        for match in safe:
            eligibility_score = self._compute_eligibility_match_score(profile, match.scheme)
            final_score = round(
                SEMANTIC_WEIGHT * match.match_score + ELIGIBILITY_WEIGHT * eligibility_score, 4
            )
            explanation = self._generate_match_explanation(profile, match.scheme)
            ranked.append(SchemeMatch(
                scheme=match.scheme,
                match_score=final_score,
                eligibility_explanation=explanation,
            ))

        ranked.sort(key=lambda m: m.match_score, reverse=True)
        logger.info("Ranker produced %d ranked matches for '%s'", len(ranked), profile.business_name)
        return ranked

    def _compute_eligibility_match_score(
        self, profile: BusinessProfile, scheme: SchemeDocument
    ) -> float:
        """Score 0-1 based on how many soft criteria the profile meets.

        Soft criteria are desirable but not required (hard requirements were
        already enforced by the constraint filter). Each criterion that applies
        and is met adds to the score.
        """
        criteria_met = 0
        criteria_total = 0

        # Criterion 1: sector in target_segments
        criteria_total += 1
        if profile.sector.lower() in [s.lower() for s in scheme.target_segments]:
            criteria_met += 1

        # Criterion 2: has collateral (bonus even if not required)
        criteria_total += 1
        if profile.has_collateral:
            criteria_met += 1

        # Criterion 3: GST filing rate is strong (≥ 80%)
        criteria_total += 1
        if profile.gst_filing_rate_pct >= 80.0:
            criteria_met += 1

        # Criterion 4: vintage well above minimum (2x the minimum or ≥ 24 months)
        criteria_total += 1
        min_vintage = scheme.eligibility_vintage_months_min
        threshold = max(min_vintage * 2, 24)
        if profile.vintage_months >= threshold:
            criteria_met += 1

        # Criterion 5: loan amount in lower 75% of scheme range (safer to approve)
        criteria_total += 1
        if scheme.loan_range_max > 0:
            range_span = scheme.loan_range_max - scheme.loan_range_min
            upper_75 = scheme.loan_range_min + 0.75 * range_span
            if profile.loan_amount_sought_inr <= upper_75:
                criteria_met += 1

        return round(criteria_met / criteria_total, 4)

    def _generate_match_explanation(
        self, profile: BusinessProfile, scheme: SchemeDocument
    ) -> str:
        """Generate a plain-English explanation of why this scheme suits the profile."""
        parts = []

        parts.append(f"{scheme.name} is administered by {scheme.administered_by}.")

        if not scheme.collateral_required:
            parts.append("No collateral is required.")
        elif profile.has_collateral:
            parts.append("Your collateral meets the scheme's requirements.")

        if scheme.loan_range_max == 0:
            parts.append("This is a subsidy or support scheme with no loan component.")
        else:
            min_l = int(scheme.loan_range_min)
            max_l = int(scheme.loan_range_max)
            parts.append(
                f"Loan range is ₹{min_l:,} to ₹{max_l:,}; "
                f"you are seeking ₹{int(profile.loan_amount_sought_inr):,}."
            )

        if scheme.interest_rate_min == 0 and scheme.interest_rate_max == 0:
            parts.append("Interest rate is set by the lending institution.")
        else:
            parts.append(
                f"Interest rate: {scheme.interest_rate_min}%–{scheme.interest_rate_max}%."
            )

        if scheme.eligibility_vintage_months_min > 0:
            parts.append(
                f"Requires {scheme.eligibility_vintage_months_min} months in business; "
                f"your business has {profile.vintage_months} months."
            )

        if profile.sector.lower() in [s.lower() for s in scheme.target_segments]:
            parts.append(f"Your sector ({profile.sector}) is a target segment for this scheme.")

        return " ".join(parts)