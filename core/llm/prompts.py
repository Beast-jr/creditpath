"""LLM prompt templates. Finalized via documented iteration — see docs/prompt_iterations.md.

Two prompts only, matching the two LLM calls per assessment:
  Call 1 — ASSESSMENT_EXPLANATION_PROMPT (this file, Day 19)
  Call 2 — IMPROVEMENT_PLAN_PROMPT       (Day 20)

Do not edit these casually. Any change must be re-tested against at least five
golden personas and logged in docs/prompt_iterations.md.
"""

# ---------------------------------------------------------------------------
# Call 1 — Assessment explainer
#
# Finalized at iteration 9. Design constraints, each traceable to a failure
# observed during iteration:
#   - "NOT the lender"          : model wrote "our loan officer" (iter 6)
#   - "no score fractions"      : model dumped "20/100" at the owner (iter 6)
#   - "never invent a figure"   : model hallucinated a Rs 15,000 sales target (iter 3)
#   - "owner ALONE"             : model told a shopkeeper to hire an advisor (iter 7)
#   - "no markdown"             : model emitted **NEARLY_READY** (spot-check)
#   - "plain English tier/rating": model leaked raw enums NEARLY_READY, ADEQUATE,
#                                   MEDIUM risk, and raw ratios like "0.27" (iter 9)
#   - "route to fixable weakness": unchangeable weaknesses (sector, vintage) produced
#                                   vague fallback actions (iter 9)
# ---------------------------------------------------------------------------
ASSESSMENT_EXPLANATION_PROMPT = """You advise small shop owners in India on loan readiness. Many did not finish school and have no accountant. You are NOT the lender — never say we, our bank, or our loan officer.

Explain this assessment. 4 short sentences. Last one is a priority action.

Rules:
- Write tier and rating words in plain English (say "nearly ready", not "NEARLY_READY" or "ADEQUATE").
- No score fractions for dimensions. Say weakest area / second weakest.
- If you mention a ratio or number, explain what it means in the same sentence.
- Explain any banking term in the same sentence, in everyday words.
- If the weakest area cannot be changed by the owner (like business age or sector type), say so honestly and make the priority action target the most fixable weakness instead.
- Action must be doable by the owner ALONE — no accountant, advisor, consultant, or financial statements.
- Only use numbers given. Never invent a figure, target, or projection.
- Plain text only. No markdown, no asterisks.
- No: consider, you may want to, as an AI, financial advisor, cash flow statement.

Data:
Business: {business_name}, {sector}, {city}
Loan sought: Rs {loan_amount:,}
Score: {score}/100 — {tier}
Weakest: {weakest_1_name} — {weakest_1_reason}
Second: {weakest_2_name} — {weakest_2_reason}

Explanation:"""


# Phrases that indicate the model ignored the prompt. Day 21's explainer
# retries the call if any of these appear in the response.
REFUSAL_PHRASES = [
    "as an ai",
    "i cannot",
    "i'm unable",
    "i am unable",
    "you may want to consider",
    "financial advisor",
    "consult a professional",
]
