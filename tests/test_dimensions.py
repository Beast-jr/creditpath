"""Unit tests for the first three dimension scorers: best, worst, boundary, middle."""

from core.schema import BusinessProfile
from core.scorecard.dimensions import (
    score_cash_flow_consistency,
    score_debt_service_coverage,
    score_gst_regularity,
)


def _profile(**overrides) -> BusinessProfile:
    """Baseline valid profile; override only the field under test."""
    base = dict(
        business_name="Test", owner_name="T", sector="retail", city="X", state="Y",
        geographic_tier=2, monthly_revenue_inr=400000.0, revenue_consistency_pct=75.0,
        existing_emi_inr=50000.0, gst_filing_rate_pct=80.0, vintage_months=24,
        has_collateral=True, collateral_value_inr=500000.0, loan_amount_sought_inr=1000000.0,
    )
    base.update(overrides)
    return BusinessProfile(**base)


# --- Cash flow consistency ---
def test_cash_flow_strong():
    assert score_cash_flow_consistency(_profile(revenue_consistency_pct=95)).score == 90.0

def test_cash_flow_critical():
    assert score_cash_flow_consistency(_profile(revenue_consistency_pct=30)).score == 20.0

def test_cash_flow_boundary_85():
    assert score_cash_flow_consistency(_profile(revenue_consistency_pct=85)).score == 90.0

def test_cash_flow_middle():
    assert score_cash_flow_consistency(_profile(revenue_consistency_pct=72)).score == 70.0


# --- DSCR ---
def test_dscr_strong_no_emi():
    assert score_debt_service_coverage(_profile(existing_emi_inr=0)).score == 90.0

def test_dscr_critical():
    # 0.2*400000/95000 = 0.84 -> CRITICAL
    assert score_debt_service_coverage(_profile(existing_emi_inr=95000)).score == 20.0

def test_dscr_boundary_1_0():
    # net=80000; emi=80000 -> DSCR 1.0 -> WEAK
    assert score_debt_service_coverage(_profile(existing_emi_inr=80000)).score == 45.0

def test_dscr_adequate():
    # net=80000; emi=50000 -> DSCR 1.6 -> ADEQUATE
    assert score_debt_service_coverage(_profile(existing_emi_inr=50000)).score == 70.0


# --- GST ---
def test_gst_strong():
    assert score_gst_regularity(_profile(gst_filing_rate_pct=95)).score == 90.0

def test_gst_critical():
    assert score_gst_regularity(_profile(gst_filing_rate_pct=40)).score == 20.0

def test_gst_boundary_75():
    assert score_gst_regularity(_profile(gst_filing_rate_pct=75)).score == 70.0

def test_gst_middle():
    assert score_gst_regularity(_profile(gst_filing_rate_pct=60)).score == 45.0