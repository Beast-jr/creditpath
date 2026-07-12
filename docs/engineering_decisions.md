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
---

## ADR-006: 36 structured JSON documents over a larger unstructured corpus

**Context:** The recommendation engine needs a knowledge base of government
financing schemes for Indian MSMEs. Two approaches were considered: scrape
hundreds of pages from government portals into raw text and rely on pure
semantic search, or curate a smaller set of structured JSON documents validated
against a strict schema.

**Decision:** 36 hand-curated JSON documents, each validated against a JSON
Schema (Draft-07) with `additionalProperties: false`.

**Alternatives considered:** A large scraped corpus — rejected for three reasons.
First, the constraint filter needs typed fields (numeric loan ranges, boolean
collateral flags, sector lists, vintage minimums) to eliminate ineligible schemes
deterministically; parsing these from free text would require an extraction step
that introduces errors. Second, scraped government pages contain navigation chrome,
disclaimers, and boilerplate that pollute embeddings; the hand-written
`retrieval_text` field gives the sentence-transformer a clean, dense target.
Third, MSME lending in India is dominated by a known set of programmes (MUDRA,
CGTMSE, Stand-Up India, SIDBI direct, plus state-level interest subsidy and
term loan schemes) — 36 documents cover this universe without padding.

**Consequences:** Adding a scheme means creating a validated JSON file and
re-running the embedding pipeline — intentional friction that keeps data quality
high. If the scheme landscape shifts significantly, the KB must be manually
updated, which is acceptable at this project's scale.
---

## ADR-006: 36 structured JSON documents over a larger unstructured corpus

**Status:** Accepted
**Date:** 2026-07-12

**Context:** The recommendation engine needs a knowledge base of government
financing schemes for Indian MSMEs. Two approaches were considered: scrape
hundreds of pages from government portals into raw text and rely on pure
semantic search, or curate a smaller set of structured JSON documents validated
against a strict schema.

**Decision:** 36 hand-curated JSON documents, each validated against a JSON
Schema (Draft-07) with additionalProperties: false.

**Alternatives considered:** A large scraped corpus — rejected for three reasons.
First, the constraint filter needs typed fields (numeric loan ranges, boolean
collateral flags, sector lists, vintage minimums) to eliminate ineligible schemes
deterministically; parsing these from free text introduces errors. Second,
scraped government pages contain navigation chrome and boilerplate that pollute
embeddings; the hand-written retrieval_text field gives the sentence-transformer
a clean, dense target. Third, MSME lending in India is dominated by a known set
of programmes — 36 documents cover this universe without padding.

**Consequences:** Adding a scheme requires creating a validated JSON file and
re-running the embedding pipeline — intentional friction that keeps data quality
high. URL verification (scripts/verify_urls.py) shows 33/36 URLs return HTTP 200;
the 3 remaining (clcss.dcmsme.gov.in, standupmitra.in, udyamregistration.gov.in)
are confirmed-correct official URLs that block automated requests with 503/403
responses but load normally in browsers. These are documented here and accepted.
# paste adr_007_append.md contents here

---

## ADR-007: Hybrid retrieval scoring (60% semantic, 40% eligibility)

**Status:** Accepted
**Date:** 2026-07-12

**Context:** After hard eligibility filtering, multiple schemes remain eligible
for a given profile. We need a ranking function that surfaces the most relevant
and best-fitting schemes at the top.

**Decision:** Two-component hybrid score:
- 60% semantic similarity (ChromaDB L2 distance on retrieval_text embeddings)
- 40% eligibility match score (fraction of 5 soft criteria met)

**Alternatives considered:**

Pure semantic ranking — rejected because two schemes with identical semantic
similarity scores may differ significantly in fit: one may cover the exact loan
range sought, the other may not. Semantic similarity alone cannot distinguish this.

Pure rule scoring — rejected because it cannot differentiate between schemes that
all pass the same soft criteria. Semantic similarity breaks ties in a principled
way and surfaces schemes whose descriptions match the business's actual context.

Equal 50/50 split — considered but semantic similarity is a richer signal (trained
on millions of text pairs) while the eligibility score is computed from only 5
hand-crafted criteria. Giving semantic the larger weight produces better-ordered
results in manual spot-checks across the 20 golden personas.

**Soft criteria scored (eligibility match score):**
1. Profile sector in scheme's target_segments
2. Profile has collateral (bonus even if not required)
3. GST filing rate >= 80%
4. Vintage >= 2x the scheme minimum or >= 24 months
5. Loan amount in lower 75% of scheme range

**Consequences:** Weights are documented constants in ranker.py with an import-time
assert that they sum to 1.0. Changing the split requires updating one line.
The formula is verified by a unit test that checks the exact arithmetic.
