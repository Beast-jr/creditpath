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
# Dimension names (continued)
DIM_VINTAGE = "Business Vintage"
DIM_SECTORAL = "Sectoral Risk"
DIM_COLLATERAL = "Collateral Availability"

# --- Business vintage thresholds (months) ---
VINTAGE_STRONG_MIN = 60
VINTAGE_ADEQUATE_MIN = 36
VINTAGE_WEAK_MIN = 12

# --- Sectoral risk ---
# Band scores are distinct from the shared 90/70/45/20 set per design doc.
SECTOR_SCORE_LOW = 90.0
SECTOR_SCORE_MEDIUM = 65.0
SECTOR_SCORE_HIGH = 40.0
SECTOR_SCORE_VERY_HIGH = 20.0

SECTOR_RISK_DEFAULT = "MEDIUM"   # unknown sectors -> neutral

# Sector name (lowercased) -> risk tier
SECTOR_RISK_TABLE = {
    "essential retail": "LOW",
    "food": "LOW",
    "grocery": "LOW",
    "healthcare": "LOW",
    "pharmacy": "LOW",
    "manufacturing": "MEDIUM",
    "auto-parts retail": "MEDIUM",
    "auto-parts": "MEDIUM",
    "retail": "MEDIUM",
    "services": "MEDIUM",
    "textile": "MEDIUM",
    "construction": "HIGH",
    "hospitality": "HIGH",
    "restaurant": "HIGH",
    "discretionary retail": "HIGH",
    "speculative": "VERY_HIGH",
}

SECTOR_TIER_TO_SCORE = {
    "LOW": (SECTOR_SCORE_LOW, LABEL_STRONG),
    "MEDIUM": (SECTOR_SCORE_MEDIUM, LABEL_ADEQUATE),
    "HIGH": (SECTOR_SCORE_HIGH, LABEL_WEAK),
    "VERY_HIGH": (SECTOR_SCORE_VERY_HIGH, LABEL_CRITICAL),
}

# --- Collateral coverage thresholds (collateral_value / loan_sought) ---
COLLATERAL_STRONG_MIN = 1.0
COLLATERAL_ADEQUATE_MIN = 0.5
COLLATERAL_WEAK_MIN = 0.01