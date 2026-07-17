# Ablation Report: Dense-Only vs Hybrid Retrieval

**Date:** 2026-07-17
**Evaluator:** Custom IR metrics (no LLM dependency)
**Ground truth:** 40 queries across 20 golden personas (2 per persona)
**Embedding model:** all-MiniLM-L6-v2 (local)

## Results

| Metric | Dense-Only | Hybrid | Delta |
|---|---|---|---|
| hit_rate | 0.725 | 1.000 | +0.275 |
| precision_at_5 | 0.195 | 0.395 | +0.200 |
| mean_reciprocal_rank | 0.390 | 0.673 | +0.283 |
| absent_violation_rate | 0.025 | 0.000 | -0.025 |

## Config A: Dense-Only
Semantic similarity only using all-MiniLM-L6-v2 embeddings against ChromaDB.
No eligibility weighting. Constraint filter still applied (hard rules only).

## Config B: Full Hybrid Pipeline
Combines semantic similarity (0.6 weight) with eligibility matching (0.4 weight).
Eligibility score computed from 5 soft criteria: sector match, collateral,
GST compliance, vintage, and loan amount fit.

## Analysis

**Hit rate (+27.5pp):** Dense-only misses 11 of 40 queries entirely. These failures
cluster around state-specific schemes where retrieval_text is semantically similar
across schemes but eligibility criteria differ sharply. The eligibility score
component correctly surfaces the geographically relevant scheme when semantic
similarity alone cannot distinguish.

**Precision@5 (+20pp):** Dense-only returns many semantically plausible but
ineligible schemes whose loan range or vintage requirements exclude the profile.
The 0.4 eligibility weight penalises these, pushing genuinely eligible schemes higher.

**Mean Reciprocal Rank (+28.3pp):** Dense-only MRR of 0.39 means the first correct
scheme appears on average at rank 2.6. Hybrid MRR of 0.67 means it appears at rank
1.5 on average, nearly always in the top 2.

**Absent violation rate (-2.5pp):** Dense-only surfaces at least one banned scheme
in 1 of 40 queries. Hybrid eliminates this entirely.

## Conclusion

The 60/40 hybrid weighting (ADR-007) is validated. The eligibility component
provides meaningful signal beyond pure semantic similarity, particularly for
state-specific schemes and profiles with hard eligibility constraints.
Hybrid is superior across all four metrics.
