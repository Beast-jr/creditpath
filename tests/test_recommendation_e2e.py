# paste test_recommendation_e2e.py contents here
"""End-to-end recommendation tests against all 20 golden personas.

For every persona, asserts:
1. At least 1 scheme returned
2. No returned scheme violates hard eligibility constraints
3. Every explanation references at least one specific field value from the profile/scheme
"""

import json
from pathlib import Path

import pytest

from core.recommendation.engine import RecommendationEngine
from core.recommendation.filter import ConstraintFilter
from core.schema import BusinessProfile, SchemeMatch

GOLDEN_PATH = Path("tests/fixtures/golden_personas.json")
GOLDEN_PERSONAS = json.loads(GOLDEN_PATH.read_text())

# Load engine once for the whole session — model load is slow
@pytest.fixture(scope="module")
def engine():
    return RecommendationEngine()


def _make_profile(persona: dict) -> BusinessProfile:
    data = {k: v for k, v in persona.items() if k != "expected_tier"}
    return BusinessProfile(**data)


# ── Parametrized e2e tests ────────────────────────────────────────

@pytest.mark.parametrize(
    "persona",
    GOLDEN_PERSONAS,
    ids=[p["business_name"] for p in GOLDEN_PERSONAS],
)
def test_at_least_one_scheme_returned(engine, persona):
    """Every golden persona must receive at least 1 recommendation."""
    profile = _make_profile(persona)
    result = engine.recommend(profile, top_k=5)
    assert len(result.matches) >= 1, (
        f"{persona['business_name']} received 0 recommendations"
    )


@pytest.mark.parametrize(
    "persona",
    GOLDEN_PERSONAS,
    ids=[p["business_name"] for p in GOLDEN_PERSONAS],
)
def test_no_hard_constraint_violated(persona):
    """No returned scheme may violate the constraint filter's hard rules."""
    profile = _make_profile(persona)
    engine = RecommendationEngine()
    result = engine.recommend(profile, top_k=5)
    cf = ConstraintFilter()

    for match in result.matches:
        scheme = match.scheme

        # Vintage
        assert profile.vintage_months >= scheme.eligibility_vintage_months_min, (
            f"{persona['business_name']}: {scheme.scheme_id} requires "
            f"{scheme.eligibility_vintage_months_min} months vintage but profile has "
            f"{profile.vintage_months}"
        )

        # Loan amount (skip pure subsidy schemes with 0/0)
        if not (scheme.loan_range_min == 0 and scheme.loan_range_max == 0):
            assert scheme.loan_range_min <= profile.loan_amount_sought_inr <= scheme.loan_range_max, (
                f"{persona['business_name']}: {scheme.scheme_id} loan range "
                f"{scheme.loan_range_min}-{scheme.loan_range_max} but profile seeks "
                f"{profile.loan_amount_sought_inr}"
            )

        # Collateral
        if scheme.collateral_required:
            assert profile.has_collateral, (
                f"{persona['business_name']}: {scheme.scheme_id} requires collateral "
                f"but profile has none"
            )

        # Sector exclusion
        excluded = [s.lower() for s in scheme.eligibility_sectors_excluded]
        assert profile.sector.lower() not in excluded, (
            f"{persona['business_name']}: {scheme.scheme_id} excludes sector "
            f"'{profile.sector}'"
        )

        # Sector inclusion (if restricted)
        included = [s.lower() for s in scheme.eligibility_sectors_included]
        if included:
            assert profile.sector.lower() in included, (
                f"{persona['business_name']}: {scheme.scheme_id} only allows "
                f"{included} but profile sector is '{profile.sector}'"
            )

        # Geography
        restriction = scheme.eligibility_geographic_restriction.strip()
        if restriction:
            assert profile.state.lower() == restriction.lower(), (
                f"{persona['business_name']}: {scheme.scheme_id} restricted to "
                f"'{restriction}' but profile state is '{profile.state}'"
            )

        # GST
        if scheme.eligibility_gst_required:
            assert profile.gst_filing_rate_pct > 0, (
                f"{persona['business_name']}: {scheme.scheme_id} requires GST "
                f"but profile has 0% filing rate"
            )


@pytest.mark.parametrize(
    "persona",
    GOLDEN_PERSONAS,
    ids=[p["business_name"] for p in GOLDEN_PERSONAS],
)
def test_explanations_reference_specific_values(engine, persona):
    """Every explanation must contain at least one specific field value."""
    profile = _make_profile(persona)
    result = engine.recommend(profile, top_k=5)

    for match in result.matches:
        explanation = match.eligibility_explanation
        assert len(explanation) > 0, (
            f"{persona['business_name']}: empty explanation for {match.scheme.scheme_id}"
        )
        # Explanation must reference at least one of: scheme name, administered_by,
        # a numeric value, or a field from the profile
        has_specific_value = any([
            match.scheme.name in explanation,
            match.scheme.administered_by in explanation,
            str(int(profile.loan_amount_sought_inr)) in explanation.replace(",", ""),
            profile.sector.lower() in explanation.lower(),
            str(profile.vintage_months) in explanation,
        ])
        assert has_specific_value, (
            f"{persona['business_name']}: explanation for {match.scheme.scheme_id} "
            f"contains no specific field values: '{explanation[:100]}'"
        )


# ── Pipeline-level assertions ────────────────────────────────────

def test_total_found_always_gte_matches(engine):
    """total_found must always be >= number of matches returned."""
    for persona in GOLDEN_PERSONAS:
        profile = _make_profile(persona)
        result = engine.recommend(profile, top_k=5)
        assert result.total_found >= len(result.matches), (
            f"{persona['business_name']}: total_found {result.total_found} < "
            f"matches {len(result.matches)}"
        )


def test_match_scores_sorted_descending(engine):
    """Results must be ordered best-first for every persona."""
    for persona in GOLDEN_PERSONAS:
        profile = _make_profile(persona)
        result = engine.recommend(profile, top_k=5)
        scores = [m.match_score for m in result.matches]
        assert scores == sorted(scores, reverse=True), (
            f"{persona['business_name']}: results not sorted descending: {scores}"
        )


def test_all_scores_in_range(engine):
    """All match scores must be in [0, 1]."""
    for persona in GOLDEN_PERSONAS:
        profile = _make_profile(persona)
        result = engine.recommend(profile, top_k=5)
        for match in result.matches:
            assert 0.0 <= match.match_score <= 1.0, (
                f"{persona['business_name']}: score {match.match_score} out of range"
            )