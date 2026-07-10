# Engineering Decisions (ADRs)

## ADR-001: Scorecard over ML model

**Context:** We need to assess MSME loan readiness. The obvious instinct is to
train a classifier.

**Decision:** Use a transparent, rule-based weighted scorecard.

**Alternatives considered:** A trained ML credit model — rejected because MSME
credit-outcome data isn't publicly available. Training on synthetic data yields
a model that only re-learns the rules we invented to generate it, adding opacity
with zero real signal.

**Consequences:** Every score is explainable and defensible line by line, which
matches what real small-ticket lenders (SIDBI, CGTMSE) actually use. Harder to
capture subtle non-linear interactions, but for this segment transparency
outweighs marginal accuracy.

---

## ADR-002: Hybrid retrieval over pure vector search

**Context:** We recommend financing schemes from a 35-document knowledge base.
Users must not see schemes they legally cannot qualify for.

**Decision:** Two-stage retrieval — a hard constraint filter first (eliminates
ineligible schemes), then dense vector retrieval to rank the survivors by
semantic relevance.

**Alternatives considered:** Pure vector search — rejected because semantic
similarity can rank an ineligible scheme above an eligible one (e.g. a
manufacturing-only scheme surfacing for a retailer). Pure rule filtering —
rejected because it can't rank by relevance once several schemes qualify.

**Consequences:** Each stage covers the other's failure mode: the filter
guarantees eligibility, the vector stage guarantees relevance. Slightly more
code and two components to maintain, but recommendations are both correct and
well-ordered.

---

## ADR-003: Constrained LLM usage (two calls only)

**Context:** LLMs add fluent language but introduce hallucination risk in a
financial domain.

**Decision:** Use the LLM in exactly two places — the plain-English explainer
(Call 1) and the structured improvement planner (Call 2). Everything else is
deterministic.

**Alternatives considered:** LLM-driven scoring or retrieval — rejected as
unverifiable and unsafe for credit guidance. A chat interface — rejected as
scope creep that invites hallucinated financial advice.

**Consequences:** The system stays auditable; scores and eligibility never
depend on model output. The planner's JSON is schema-enforced with retry. Fewer
"magic" features, but every number the user sees is traceable.

---

## ADR-004: FastAPI as the API layer

**Context:** Streamlit could call core/ directly in-process. Why add an API?

**Decision:** Put a FastAPI layer between Streamlit and core/, with route
handlers holding zero business logic (deserialize → call core/ → serialize).

**Alternatives considered:** Streamlit calling core/ directly — rejected because
it welds the UI to the logic; no other client could reuse it. A heavier
framework (Django) — rejected as overkill for a handful of endpoints.

**Consequences:** core/ is reusable by any future client (React, mobile) with no
changes. FastAPI auto-generates Swagger docs at /docs — a free professional
touch. One more process to run and deploy (Railway), which is acceptable.