"""First three dimension scorers. Pure functions: profile in, DimensionScore out."""

from core.schema import BusinessProfile, DimensionScore
from core.scorecard import constants as c


def score_cash_flow_consistency(profile: BusinessProfile) -> DimensionScore:
    """Score revenue stability from revenue_consistency_pct."""
    pct = profile.revenue_consistency_pct
    if pct >= c.CASH_FLOW_STRONG_MIN:
        score, label, band = c.SCORE_STRONG, c.LABEL_STRONG, "STRONG (>=85)"
    elif pct >= c.CASH_FLOW_ADEQUATE_MIN:
        score, label, band = c.SCORE_ADEQUATE, c.LABEL_ADEQUATE, "ADEQUATE (70-84)"
    elif pct >= c.CASH_FLOW_WEAK_MIN:
        score, label, band = c.SCORE_WEAK, c.LABEL_WEAK, "WEAK (50-69)"
    else:
        score, label, band = c.SCORE_CRITICAL, c.LABEL_CRITICAL, "CRITICAL (<50)"
    return DimensionScore(
        dimension_name=c.DIM_CASH_FLOW,
        score=score,
        label=label,
        reason=f"Revenue consistency {pct:.0f}% in {band} band.",
    )


def score_debt_service_coverage(profile: BusinessProfile) -> DimensionScore:
    """Score EMI burden. DSCR = (net margin x revenue) / existing EMI."""
    net_revenue = c.DSCR_NET_MARGIN * profile.monthly_revenue_inr
    if profile.existing_emi_inr <= 0:
        dscr = float("inf")
    else:
        dscr = net_revenue / profile.existing_emi_inr

    if dscr >= c.DSCR_STRONG_MIN:
        score, label = c.SCORE_STRONG, c.LABEL_STRONG
    elif dscr >= c.DSCR_ADEQUATE_MIN:
        score, label = c.SCORE_ADEQUATE, c.LABEL_ADEQUATE
    elif dscr >= c.DSCR_WEAK_MIN:
        score, label = c.SCORE_WEAK, c.LABEL_WEAK
    else:
        score, label = c.SCORE_CRITICAL, c.LABEL_CRITICAL

    dscr_str = "no existing EMI" if profile.existing_emi_inr <= 0 else f"DSCR {dscr:.2f}"
    return DimensionScore(
        dimension_name=c.DIM_DSCR,
        score=score,
        label=label,
        reason=f"{dscr_str}; {label} coverage of existing debt.",
    )


def score_gst_regularity(profile: BusinessProfile) -> DimensionScore:
    """Score compliance discipline from gst_filing_rate_pct."""
    pct = profile.gst_filing_rate_pct
    if pct >= c.GST_STRONG_MIN:
        score, label, band = c.SCORE_STRONG, c.LABEL_STRONG, "STRONG (>=90)"
    elif pct >= c.GST_ADEQUATE_MIN:
        score, label, band = c.SCORE_ADEQUATE, c.LABEL_ADEQUATE, "ADEQUATE (75-89)"
    elif pct >= c.GST_WEAK_MIN:
        score, label, band = c.SCORE_WEAK, c.LABEL_WEAK, "WEAK (50-74)"
    else:
        score, label, band = c.SCORE_CRITICAL, c.LABEL_CRITICAL, "CRITICAL (<50)"
    return DimensionScore(
        dimension_name=c.DIM_GST,
        score=score,
        label=label,
        reason=f"GST filing {pct:.0f}% in {band} band.",
    )