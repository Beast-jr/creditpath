# Scheme Knowledge Base — Coverage Matrix

The 35 scheme documents must collectively span the dimensions below so
recommendations aren't lopsided. Targets are minimums, not quotas.

## By source (35 total)
| Source | Count | Days |
|---|---|---|
| Central government | 18 | Day 11 |
| State government + SIDBI | 17 | Day 12 |

## By scheme_type (target spread)
| Type | Min docs |
|---|---|
| term_loan | 8 |
| working_capital | 7 |
| credit_guarantee | 5 |
| subsidy | 6 |
| composite | 6 |
| equity | 3 |

## By target segment
| Segment | Must be covered |
|---|---|
| Micro (< ₹1 Cr turnover) | yes |
| Small (₹1–10 Cr) | yes |
| Medium (₹10–50 Cr) | yes |
| Women-owned | yes |
| SC/ST entrepreneurs | yes |
| First-generation / no collateral | yes |
| Manufacturing | yes |
| Services / trading | yes |

## By loan size
| Band | Must be covered |
|---|---|
| < ₹5 lakh (micro) | yes |
| ₹5–50 lakh | yes |
| ₹50 lakh – ₹5 Cr | yes |
| > ₹5 Cr | yes |

## By geography
| Scope | Must be covered |
|---|---|
| Pan-India (no restriction) | majority |
| State-specific | at least 8 states |
| Tier-2 / tier-3 focus | yes |

## Collateral profile
- At least 6 schemes with `collateral_required: false` (CGTMSE-style) — the
  core segment CreditPath serves.

## Verification rule
Every scheme's `official_url` must resolve to a government/SIDBI/bank source,
and `last_verified_date` set when the document is written. Re-checked on Day 13.