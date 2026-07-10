"""Edge-case and validation tests for the scorecard engine."""

import pytest

from core.schema import BusinessProfile
from core.scorecard.engine import score_business


def _profile(**overrides) -> BusinessProfile:
    base = dict(
        business_name="T", owner_name="T", sector="retail", city="X", state="Y",
        geographic_tier=2, monthly_revenue_inr=400000.0, revenue_consistency_pct=75.0,
        existing_emi_inr=50000.0, gst_filing_rate_pct=80.0, vintage_months=24,
        has_collateral=True, collateral_value_inr=500000.0, loan_amount_sought_inr=1000000.0,
    )
    base.update(overrides)
    return BusinessProfile(**base)


def test_zero_revenue_rejected():
    with pytest.raises(ValueError):
        score_business(_profile(monthly_revenue_inr=0))

def test_negative_vintage_rejected():
    with pytest.raises(ValueError):
        score_business(_profile(vintage_months=-1))

def test_gst_over_100_rejected():
    with pytest.raises(ValueError):
        score_business(_profile(gst_filing_rate_pct=150))

def test_bad_geographic_tier_rejected():
    with pytest.raises(ValueError):
        score_business(_profile(geographic_tier=5))

def test_zero_loan_rejected():
    with pytest.raises(ValueError):
        score_business(_profile(loan_amount_sought_inr=0))

def test_score_bounds_valid_profile():
    result = score_business(_profile())
    assert 0.0 <= result.weighted_score <= 100.0

def test_all_minimum_valid_inputs():
    # Weakest legal profile shouldn't crash; should land NOT_READY.
    result = score_business(_profile(
        revenue_consistency_pct=0, existing_emi_inr=999999, gst_filing_rate_pct=0,
        vintage_months=0, has_collateral=False, collateral_value_inr=0,
        sector="speculative",
    ))
    assert result.tier == "NOT_READY"