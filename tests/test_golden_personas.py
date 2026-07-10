"""Regression suite: freezes engine output across 20 golden personas.

Run directly (python -m tests.test_golden_personas) to regenerate the frozen
baseline; run via pytest to assert the engine still matches it.
"""

import json
from pathlib import Path

from core.schema import BusinessProfile
from core.scorecard.engine import score_business

FIXTURE = Path("tests/fixtures/golden_personas.json")
BASELINE = Path("tests/fixtures/golden_baseline.json")

PROFILE_FIELDS = {
    "business_name", "owner_name", "sector", "city", "state", "geographic_tier",
    "monthly_revenue_inr", "revenue_consistency_pct", "existing_emi_inr",
    "gst_filing_rate_pct", "vintage_months", "has_collateral",
    "collateral_value_inr", "loan_amount_sought_inr",
}


def _load_personas() -> list:
    with open(FIXTURE) as f:
        return json.load(f)


def _to_profile(persona: dict) -> BusinessProfile:
    return BusinessProfile(**{k: persona[k] for k in PROFILE_FIELDS})


def regenerate_baseline() -> None:
    """Score all personas and freeze weighted_score + tier as the baseline."""
    out = []
    for p in _load_personas():
        result = score_business(_to_profile(p))
        assert result.tier == p["expected_tier"], (
            f"{p['business_name']}: engine tier {result.tier} != expected {p['expected_tier']}"
        )
        out.append({
            "business_name": p["business_name"],
            "weighted_score": result.weighted_score,
            "tier": result.tier,
        })
    with open(BASELINE, "w") as f:
        json.dump(out, f, indent=2)
    print(f"Baseline written: {len(out)} personas, all tiers match expected.")


def test_personas_match_baseline():
    """Engine output must still match the frozen baseline for every persona."""
    with open(BASELINE) as f:
        baseline = {b["business_name"]: b for b in json.load(f)}
    for p in _load_personas():
        result = score_business(_to_profile(p))
        expected = baseline[p["business_name"]]
        assert result.weighted_score == expected["weighted_score"], p["business_name"]
        assert result.tier == expected["tier"], p["business_name"]


def test_all_expected_tiers_present():
    """Sanity: the persona set spans all four tiers."""
    tiers = {p["expected_tier"] for p in _load_personas()}
    assert tiers == {"LOAN_READY", "NEARLY_READY", "NEEDS_WORK", "NOT_READY"}


if __name__ == "__main__":
    regenerate_baseline()