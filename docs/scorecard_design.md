## Dimension 1 — Cash Flow Consistency

**Weight:** 0.25 (joint-highest)

**Definition:** How stable the business's revenue is month-to-month, expressed
as a consistency percentage (0–100). High consistency means predictable income;
low consistency means volatile, unpredictable months.

**Why lenders care:** Repayment comes from cash flow, not from profit on paper.
A business with steady ₹4L months can service an EMI reliably; one that swings
between ₹1L and ₹7L may miss payments in the lean months even if its average
looks fine. Volatility is repayment risk. This is why it shares the top weight
with DSCR — together they measure "can this business actually pay us back."

**Input field:** `revenue_consistency_pct` (0–100)

**Scoring bands:**

| Consistency % | Score | Label | Reasoning |
|---|---|---|---|
| ≥ 85 | 90 | STRONG | Highly predictable revenue; low repayment risk |
| 70–84 | 70 | ADEQUATE | Moderate swings; manageable but watched |
| 50–69 | 45 | WEAK | Significant volatility; lean months are a concern |
| < 50 | 20 | CRITICAL | Erratic income; high risk of missed payments |

**Source:** Self-reported by the owner in the form, framed as "how much do your
monthly sales vary?" In production this would ideally come from bank-statement
analysis; for v1 it's a declared estimate.

**Worked example — Kumar Auto Spares:**
Ravi reports 72% consistency (monsoon dips in the auto-parts trade). 72 falls in
the 70–84 band → **score 70, ADEQUATE.** Reason string: "Revenue consistency 72%
in ADEQUATE band (70–84); moderate month-to-month variation."
## Dimension 2 — Debt Service Coverage Ratio (DSCR)

**Weight:** 0.25 (joint-highest)

**Definition:** Ratio of net monthly revenue available for debt service against
existing EMI obligations. DSCR = (monthly_revenue × net margin) / existing_emi.
We use a simplified net-revenue proxy of 20% of monthly revenue.

**Why lenders care:** Directly measures whether current income can absorb another
loan. A business already stretched by EMIs is a default risk regardless of how
steady its revenue is.

**Input fields:** `monthly_revenue_inr`, `existing_emi_inr`

**Scoring bands (DSCR = 0.2 × revenue / emi; if emi = 0 → STRONG):**

| DSCR | Score | Label | Reasoning |
|---|---|---|---|
| ≥ 2.0 or no EMI | 90 | STRONG | Ample headroom for new debt |
| 1.25–1.99 | 70 | ADEQUATE | Comfortable coverage |
| 1.0–1.24 | 45 | WEAK | Thin margin; little buffer |
| < 1.0 | 20 | CRITICAL | Income cannot cover existing debt |

**Source:** Computed from form inputs.

**Worked example:** (0.2 × 4,20,000) / 95,000 = 84,000 / 95,000 = 0.88.
0.88 < 1.0 → **score 20, CRITICAL.** Reason: "DSCR 0.88 below 1.0; existing EMIs
exceed available net revenue."

---

## Dimension 3 — GST Filing Regularity

**Weight:** 0.20

**Definition:** Percentage of GST returns filed on time (0–100), a proxy for
financial discipline and formalization.

**Why lenders care:** Consistent GST filing signals an organized, compliant
business with a verifiable paper trail. Gaps suggest disorganization or informal
operations — both raise underwriting cost and risk.

**Input field:** `gst_filing_rate_pct` (0–100)

**Scoring bands:**

| Filing % | Score | Label | Reasoning |
|---|---|---|---|
| ≥ 90 | 90 | STRONG | Disciplined, fully compliant |
| 75–89 | 70 | ADEQUATE | Mostly compliant; minor gaps |
| 50–74 | 45 | WEAK | Inconsistent compliance |
| < 50 | 20 | CRITICAL | Poor compliance; verification risk |

**Source:** Self-reported; verifiable against GST portal in production.

**Worked example:** 83% falls in 75–89 → **score 70, ADEQUATE.** Reason:
"GST filing 83% in ADEQUATE band (75–89); minor filing gaps."

---

## Dimension 4 — Business Vintage

**Weight:** 0.15

**Definition:** Months the business has operated. Track record.

**Why lenders care:** Survival correlates with repayment ability. Older
businesses have weathered demand cycles; new ones are unproven.

**Input field:** `vintage_months`

**Scoring bands:**

| Vintage (months) | Score | Label | Reasoning |
|---|---|---|---|
| ≥ 60 | 90 | STRONG | 5+ years; proven track record |
| 36–59 | 70 | ADEQUATE | 3–5 years; established |
| 12–35 | 45 | WEAK | 1–3 years; still proving out |
| < 12 | 20 | CRITICAL | Under a year; unproven |

**Source:** Form input.

**Worked example:** 28 months falls in 12–35 → **score 45, WEAK.** Reason:
"Vintage 28 months in WEAK band (12–35); limited operating history."

---

## Dimension 5 — Sectoral Risk

**Weight:** 0.10

**Definition:** Industry-level risk based on a fixed sector classification
(broadly aligned with RBI priority-sector and risk views).

**Why lenders care:** Some sectors default more than others regardless of the
individual business. Sector sets a baseline risk the specific profile adjusts.

**Input field:** `sector` (mapped to a risk tier in constants.py on Day 5)

**Scoring bands (by sector risk tier):**

| Sector risk tier | Score | Label | Example sectors |
|---|---|---|---|
| LOW | 90 | STRONG | Essential retail, food, healthcare |
| MEDIUM | 65 | ADEQUATE | Manufacturing, auto-parts, services |
| HIGH | 40 | WEAK | Construction, hospitality, discretionary |
| VERY_HIGH | 20 | CRITICAL | Speculative / cyclical trades |

**Source:** Fixed lookup table (Day 5 constants.py). Not user-scored.

**Worked example:** Auto-parts retail → MEDIUM → **score 65, ADEQUATE.** Reason:
"Sector 'auto-parts retail' classified MEDIUM risk."

---

## Dimension 6 — Collateral Availability

**Weight:** 0.05 (lowest)

**Definition:** Pledgeable asset value relative to the loan sought
(collateral_value / loan_sought), as a coverage ratio.

**Why lenders care:** Collateral reduces loss given default. Weighted lowest
because CreditPath targets the CGTMSE/collateral-free segment — it matters, but
readiness shouldn't hinge on owning assets, which would exclude exactly the
businesses the tool serves.

**Input fields:** `has_collateral`, `collateral_value_inr`, `loan_amount_sought_inr`

**Scoring bands (coverage = collateral / loan; no collateral → CRITICAL):**

| Coverage | Score | Label | Reasoning |
|---|---|---|---|
| ≥ 1.0 | 90 | STRONG | Fully secured |
| 0.5–0.99 | 70 | ADEQUATE | Substantially secured |
| 0.01–0.49 | 45 | WEAK | Partially secured |
| none | 20 | CRITICAL | Unsecured |

**Source:** Form inputs.

**Worked example:** 6,00,000 / 10,00,000 = 0.60 → **score 70, ADEQUATE.** Reason:
"Collateral covers 60% of loan sought; ADEQUATE band (0.5–0.99)."

---

## Weight table (sums to 1.00)

| Dimension | Weight |
|---|---|
| Cash flow consistency | 0.25 |
| Debt service coverage ratio | 0.25 |
| GST filing regularity | 0.20 |
| Business vintage | 0.15 |
| Sectoral risk | 0.10 |
| Collateral availability | 0.05 |
| **Total** | **1.00** |

## Worked example — final weighted score

| Dimension | Score | Weight | Contribution |
|---|---|---|---|
| Cash flow consistency | 70 | 0.25 | 17.50 |
| Debt service coverage | 20 | 0.25 | 5.00 |
| GST filing regularity | 70 | 0.20 | 14.00 |
| Business vintage | 45 | 0.15 | 6.75 |
| Sectoral risk | 65 | 0.10 | 6.50 |
| Collateral availability | 70 | 0.05 | 3.50 |
| **Weighted total** | | | **53.25** |

**Result:** 53.25 → **NEARLY_READY** (50–69).
**Weakest dimensions:** DSCR (20), business vintage (45).

**Interpretation:** Kumar Auto Spares is close but held back by debt burden —
existing EMIs already exceed net revenue. The clear path to LOAN_READY is
reducing or restructuring debt before borrowing more. This is exactly the kind
of specific, actionable finding the improvement planner (Day 20–21) will surface.