"""Tests for core/recommendation/filter.py

Strategy:
- Each of the 6 checks tested independently (pass + fail case)
- Combined: a profile that fails multiple checks
- Zero-match edge case: profile eligible for nothing
- Golden personas: all 20 return at least 1 scheme
"""

import json
from pathlib import Path

import pytest

from core.recommendation.filter import ConstraintFilter
from core.schema import BusinessProfile, SchemeDocument

# ── Helpers ──────────────────────────────────────────────────────

def _base_profile(**overrides) -> BusinessProfile:
    """A permissive profile that passes all checks by default."""
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
    """A permissive scheme that passes all checks by default."""
    defaults = dict(
        scheme_id="test_scheme",
        name="Test Scheme",
        administered_by="Test Bank",
        scheme_type="term_loan",
        target_segments=["micro", "small"],
        loan_range_min=100_000,
        loan_range_max=5_000_000,
        interest_rate_min=8.0,
        interest_rate_max=12.0,
        collateral_required=False,
        eligibility_vintage_months_min=0,
        eligibility_gst_required=False,
        eligibility_sectors_included=[],
        eligibility_sectors_excluded=[],
        eligibility_geographic_restriction="",
        retrieval_text="A test scheme for unit testing purposes with enough text.",
        official_url="https://example.com",
        last_verified_date="2026-07-12",
    )
    defaults.update(overrides)
    return SchemeDocument(**defaults)


def _filter_with(scheme: SchemeDocument, profile: BusinessProfile) -> bool:
    """Return True if the scheme passes the filter for this profile."""
    cf = ConstraintFilter(schemes=[scheme])
    return len(cf.filter(profile)) == 1


# ── Vintage checks ───────────────────────────────────────────────

def test_vintage_pass():
    scheme = _base_scheme(eligibility_vintage_months_min=12)
    profile = _base_profile(vintage_months=24)
    assert _filter_with(scheme, profile)


def test_vintage_fail():
    scheme = _base_scheme(eligibility_vintage_months_min=24)
    profile = _base_profile(vintage_months=6)
    assert not _filter_with(scheme, profile)


def test_vintage_exact_boundary_passes():
    scheme = _base_scheme(eligibility_vintage_months_min=12)
    profile = _base_profile(vintage_months=12)
    assert _filter_with(scheme, profile)


# ── Loan amount checks ───────────────────────────────────────────

def test_loan_amount_pass():
    scheme = _base_scheme(loan_range_min=100_000, loan_range_max=1_000_000)
    profile = _base_profile(loan_amount_sought_inr=500_000)
    assert _filter_with(scheme, profile)


def test_loan_amount_too_high_fails():
    scheme = _base_scheme(loan_range_min=100_000, loan_range_max=500_000)
    profile = _base_profile(loan_amount_sought_inr=600_000)
    assert not _filter_with(scheme, profile)


def test_loan_amount_too_low_fails():
    scheme = _base_scheme(loan_range_min=500_000, loan_range_max=5_000_000)
    profile = _base_profile(loan_amount_sought_inr=100_000)
    assert not _filter_with(scheme, profile)


def test_loan_amount_zero_zero_is_pure_subsidy_always_passes():
    """Schemes with 0/0 loan range are pure subsidy — no loan component."""
    scheme = _base_scheme(loan_range_min=0, loan_range_max=0)
    profile = _base_profile(loan_amount_sought_inr=999_999_999)
    assert _filter_with(scheme, profile)


# ── Collateral checks ────────────────────────────────────────────

def test_collateral_not_required_always_passes():
    scheme = _base_scheme(collateral_required=False)
    profile = _base_profile(has_collateral=False)
    assert _filter_with(scheme, profile)


def test_collateral_required_profile_has_it_passes():
    scheme = _base_scheme(collateral_required=True)
    profile = _base_profile(has_collateral=True)
    assert _filter_with(scheme, profile)


def test_collateral_required_profile_lacks_it_fails():
    scheme = _base_scheme(collateral_required=True)
    profile = _base_profile(has_collateral=False)
    assert not _filter_with(scheme, profile)


# ── Sector checks ────────────────────────────────────────────────

def test_sector_excluded_fails():
    scheme = _base_scheme(eligibility_sectors_excluded=["retail"])
    profile = _base_profile(sector="retail")
    assert not _filter_with(scheme, profile)


def test_sector_not_excluded_passes():
    scheme = _base_scheme(eligibility_sectors_excluded=["retail"])
    profile = _base_profile(sector="manufacturing")
    assert _filter_with(scheme, profile)


def test_sector_included_list_match_passes():
    scheme = _base_scheme(eligibility_sectors_included=["manufacturing", "textile"])
    profile = _base_profile(sector="manufacturing")
    assert _filter_with(scheme, profile)


def test_sector_included_list_no_match_fails():
    scheme = _base_scheme(eligibility_sectors_included=["manufacturing", "textile"])
    profile = _base_profile(sector="retail")
    assert not _filter_with(scheme, profile)


def test_sector_check_is_case_insensitive():
    scheme = _base_scheme(eligibility_sectors_excluded=["Retail_Trade"])
    profile = _base_profile(sector="retail_trade")
    assert not _filter_with(scheme, profile)


# ── Geography checks ─────────────────────────────────────────────

def test_geography_no_restriction_passes():
    scheme = _base_scheme(eligibility_geographic_restriction="")
    profile = _base_profile(state="maharashtra")
    assert _filter_with(scheme, profile)


def test_geography_restriction_match_passes():
    scheme = _base_scheme(eligibility_geographic_restriction="karnataka")
    profile = _base_profile(state="karnataka")
    assert _filter_with(scheme, profile)


def test_geography_restriction_mismatch_fails():
    scheme = _base_scheme(eligibility_geographic_restriction="karnataka")
    profile = _base_profile(state="maharashtra")
    assert not _filter_with(scheme, profile)


def test_geography_check_is_case_insensitive():
    scheme = _base_scheme(eligibility_geographic_restriction="Karnataka")
    profile = _base_profile(state="karnataka")
    assert _filter_with(scheme, profile)


# ── GST checks ───────────────────────────────────────────────────

def test_gst_not_required_always_passes():
    scheme = _base_scheme(eligibility_gst_required=False)
    profile = _base_profile(gst_filing_rate_pct=0.0)
    assert _filter_with(scheme, profile)


def test_gst_required_profile_has_it_passes():
    scheme = _base_scheme(eligibility_gst_required=True)
    profile = _base_profile(gst_filing_rate_pct=80.0)
    assert _filter_with(scheme, profile)


def test_gst_required_profile_lacks_it_fails():
    scheme = _base_scheme(eligibility_gst_required=True)
    profile = _base_profile(gst_filing_rate_pct=0.0)
    assert not _filter_with(scheme, profile)


# ── Combined + edge cases ────────────────────────────────────────

def test_multiple_failing_checks_still_filtered():
    """A scheme failing on vintage AND collateral is still excluded."""
    scheme = _base_scheme(
        eligibility_vintage_months_min=60,
        collateral_required=True,
    )
    profile = _base_profile(vintage_months=6, has_collateral=False)
    assert not _filter_with(scheme, profile)


def test_zero_match_edge_case():
    """A profile eligible for nothing returns empty list."""
    schemes = [
        _base_scheme(scheme_id="s1", eligibility_sectors_excluded=["retail"]),
        _base_scheme(scheme_id="s2", eligibility_sectors_excluded=["retail"]),
    ]
    profile = _base_profile(sector="retail")
    cf = ConstraintFilter(schemes=schemes)
    assert cf.filter(profile) == []


def test_all_schemes_pass_permissive_profile():
    """A maximally permissive profile should get all schemes."""
    schemes = [_base_scheme(scheme_id=f"s{i}") for i in range(5)]
    profile = _base_profile()
    cf = ConstraintFilter(schemes=schemes)
    assert len(cf.filter(profile)) == 5


# ── Golden personas: each returns at least 1 scheme ─────────────

GOLDEN_PATH = Path("tests/fixtures/golden_personas.json")
GOLDEN_PERSONAS = json.loads(GOLDEN_PATH.read_text()) if GOLDEN_PATH.exists() else []


@pytest.mark.parametrize("persona", GOLDEN_PERSONAS, ids=[p["business_name"] for p in GOLDEN_PERSONAS])
def test_golden_persona_returns_at_least_one_scheme(persona):
    """Every golden persona must match at least one real scheme."""
    persona_data = {k: v for k, v in persona.items() if k != "expected_tier"}
    profile = BusinessProfile(**persona_data)
    cf = ConstraintFilter()  # loads real 36 schemes from disk
    result = cf.filter(profile)
    assert len(result) >= 1, (
        f"{persona['business_name']} matched 0 schemes — check filter logic or scheme coverage"
    )