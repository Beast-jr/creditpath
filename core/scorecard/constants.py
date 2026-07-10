"""All scoring thresholds and band scores. Zero magic numbers allowed in dimensions.py."""

# Band scores (shared across dimensions)
SCORE_STRONG = 90.0
SCORE_ADEQUATE = 70.0
SCORE_WEAK = 45.0
SCORE_CRITICAL = 20.0

# Labels
LABEL_STRONG = "STRONG"
LABEL_ADEQUATE = "ADEQUATE"
LABEL_WEAK = "WEAK"
LABEL_CRITICAL = "CRITICAL"

# Dimension names
DIM_CASH_FLOW = "Cash Flow Consistency"
DIM_DSCR = "Debt Service Coverage Ratio"
DIM_GST = "GST Filing Regularity"

# --- Cash flow consistency thresholds (revenue_consistency_pct) ---
CASH_FLOW_STRONG_MIN = 85.0
CASH_FLOW_ADEQUATE_MIN = 70.0
CASH_FLOW_WEAK_MIN = 50.0

# --- DSCR thresholds ---
DSCR_NET_MARGIN = 0.20          # net-revenue proxy: 20% of monthly revenue
DSCR_STRONG_MIN = 2.0
DSCR_ADEQUATE_MIN = 1.25
DSCR_WEAK_MIN = 1.0

# --- GST filing thresholds (gst_filing_rate_pct) ---
GST_STRONG_MIN = 90.0
GST_ADEQUATE_MIN = 75.0
GST_WEAK_MIN = 50.0