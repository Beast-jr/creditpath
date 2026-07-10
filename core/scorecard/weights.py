"""Dimension weights. Sum MUST equal 1.0 — asserted at import time so drift fails loudly."""

WEIGHT_CASH_FLOW = 0.25
WEIGHT_DSCR = 0.25
WEIGHT_GST = 0.20
WEIGHT_VINTAGE = 0.15
WEIGHT_SECTORAL = 0.10
WEIGHT_COLLATERAL = 0.05

DIMENSION_WEIGHTS = {
    "Cash Flow Consistency": WEIGHT_CASH_FLOW,
    "Debt Service Coverage Ratio": WEIGHT_DSCR,
    "GST Filing Regularity": WEIGHT_GST,
    "Business Vintage": WEIGHT_VINTAGE,
    "Sectoral Risk": WEIGHT_SECTORAL,
    "Collateral Availability": WEIGHT_COLLATERAL,
}

# Fail loudly at import if weights ever drift from 1.0 (float-safe comparison).
assert abs(sum(DIMENSION_WEIGHTS.values()) - 1.0) < 1e-9, "Dimension weights must sum to 1.0"