"""Engine integration tests, including the design-doc worked example (Kumar Auto Spares)."""

from core.schema import BusinessProfile
from core.scorecard.engine import score_business


def _kumar() -> BusinessProfile:
    """Kumar Auto Spares — the design doc's worked example. Expected: 53.25, NEARLY_READY."""
    return BusinessProfile(
        business_name="Kumar Auto Spares", owner_name="Ravi Kumar",
        sector="auto-parts retail", city="Warangal", state="Telangana",
        geographic_tier=3, monthly_revenue_inr=420000.0, revenue_consistency_pct=72.0,
        existing_emi_inr=95000.0, gst_filing_rate_pct=83.0, vintage_months=28,
        has_collateral=True, collateral_value_inr=600000.0, loan_amount_sought_inr=1000000.0,
    )


def test_worked_example_weighted_score():
    assert score_business(_kumar()).weighted_score == 53.25

def test_worked_example_tier():
    assert score_business(_kumar()).tier == "NEARLY_READY"

def test_worked_example_weakest():
    weakest = score_business(_kumar()).weakest_dimensions
    assert "Debt Service Coverage Ratio" in weakest
    assert "Business Vintage" in weakest

def test_returns_six_dimensions():
    assert len(score_business(_kumar()).dimension_scores) == 6

def test_tier_loan_ready():
    strong = BusinessProfile(
        business_name="A", owner_name="B", sector="healthcare", city="X", state="Y",
        geographic_tier=1, monthly_revenue_inr=1000000.0, revenue_consistency_pct=95.0,
        existing_emi_inr=0.0, gst_filing_rate_pct=98.0, vintage_months=72,
        has_collateral=True, collateral_value_inr=2000000.0, loan_amount_sought_inr=1000000.0,
    )
    assert score_business(strong).tier == "LOAN_READY"

def test_execution_time_recorded():
    assert score_business(_kumar()).execution_time_ms >= 0