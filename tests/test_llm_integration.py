"""Tests for core/llm/explainer.py and core/llm/planner.py.
All tests use a mocked GeminiClient — no real API calls.
"""
import json
import pytest
from unittest.mock import MagicMock
from core.schema import (
    BusinessProfile, ScorecardResult, DimensionScore,
    ImprovementPlan, Action,
)
from core.llm.explainer import generate_explanation, _is_refusal, _template_fallback
from core.llm.planner import generate_plan, _parse_response, _validate_and_build, _template_fallback as plan_fallback

VALID_PLAN_JSON = json.dumps({
    "actions": [{
        "action_id": "A1",
        "description": "Improve debt coverage by collecting overdue payments.",
        "dimension_affected": "Debt Service Coverage Ratio",
        "expected_score_delta": 15,
        "timeline_weeks": 6,
        "effort_level": "MEDIUM",
        "specific_steps": ["List overdue customers", "Call each customer", "Agree payment dates"],
    }],
    "dependencies": [],
    "milestones": [{"title": "Initial boost", "target_week": 6, "action_ids": ["A1"]}],
    "total_expected_score_delta": 15,
    "estimated_timeline_weeks": 6,
})


@pytest.fixture
def profile():
    return BusinessProfile(
        business_name="Kumar Auto Spares",
        owner_name="Ramesh Kumar",
        sector="Automotive",
        city="Hubli",
        state="Karnataka",
        geographic_tier=2,
        monthly_revenue_inr=150000,
        revenue_consistency_pct=72.0,
        existing_emi_inr=18000,
        gst_filing_rate_pct=78.0,
        vintage_months=30,
        has_collateral=True,
        collateral_value_inr=500000,
        loan_amount_sought_inr=800000,
    )


@pytest.fixture
def scorecard():
    return ScorecardResult(
        dimension_scores=[
            DimensionScore(dimension_name="Cash Flow Consistency", score=70.0, label="ADEQUATE", reason="Revenue consistency at 72%"),
            DimensionScore(dimension_name="Debt Service Coverage Ratio", score=45.0, label="WEAK", reason="EMI burden high relative to revenue"),
            DimensionScore(dimension_name="GST Filing Regularity", score=70.0, label="ADEQUATE", reason="GST rate 78% near threshold"),
            DimensionScore(dimension_name="Business Vintage", score=45.0, label="WEAK", reason="30 months operational"),
            DimensionScore(dimension_name="Sectoral Risk", score=65.0, label="ADEQUATE", reason="Automotive medium risk"),
            DimensionScore(dimension_name="Collateral Availability", score=90.0, label="STRONG", reason="Collateral covers loan"),
        ],
        weighted_score=53.25,
        tier="NEARLY_READY",
        weakest_dimensions=["Debt Service Coverage Ratio", "Business Vintage"],
        execution_time_ms=12,
    )


@pytest.fixture
def mock_client():
    return MagicMock()


# --- Explainer tests ---

def test_explainer_returns_response_on_success(profile, scorecard, mock_client):
    mock_client.generate.return_value = "Kumar Auto Spares is nearly ready for a loan. The main weakness is high EMI burden. GST compliance is close to threshold. Focus on reducing existing debt first."
    result = generate_explanation(profile, scorecard, mock_client)
    assert len(result) > 50

def test_explainer_retries_on_refusal(profile, scorecard, mock_client):
    mock_client.generate.side_effect = [
        "As an AI I cannot provide financial advice.",
        "Kumar Auto Spares is nearly ready for a loan. EMI burden is the main weakness. Reduce existing loans before applying. Contact overdue customers this week.",
    ]
    result = generate_explanation(profile, scorecard, mock_client)
    assert "as an ai" not in result.lower()
    assert mock_client.generate.call_count == 2

def test_explainer_retries_on_short_response(profile, scorecard, mock_client):
    mock_client.generate.side_effect = [
        "Too short.",
        "Kumar Auto Spares is nearly ready for a loan. The EMI burden is the weakest area. Reducing existing loans will help the most. Call overdue customers and agree on payment dates this week.",
    ]
    result = generate_explanation(profile, scorecard, mock_client)
    assert len(result) > 50
    assert mock_client.generate.call_count == 2

def test_explainer_returns_fallback_on_total_failure(profile, scorecard, mock_client):
    mock_client.generate.side_effect = Exception("API down")
    result = generate_explanation(profile, scorecard, mock_client)
    assert isinstance(result, str)
    assert len(result) > 0

def test_explainer_fallback_contains_business_name(profile, scorecard):
    result = _template_fallback(profile, scorecard)
    assert "Kumar Auto Spares" in result

def test_is_refusal_detects_phrases():
    assert _is_refusal("As an AI I cannot help with that.")
    assert _is_refusal("I am unable to provide advice.")
    assert not _is_refusal("Kumar Auto Spares is nearly ready for a loan.")

def test_explainer_no_refusal_in_good_response(profile, scorecard, mock_client):
    mock_client.generate.return_value = "Kumar Auto Spares is nearly ready. EMI burden is the key weakness. Reduce existing loans before applying. Call overdue customers this week to agree on payment dates."
    result = generate_explanation(profile, scorecard, mock_client)
    assert not _is_refusal(result)


# --- Planner tests ---

def test_planner_returns_improvement_plan_on_success(profile, scorecard, mock_client):
    mock_client.generate.return_value = VALID_PLAN_JSON
    result = generate_plan(profile, scorecard, mock_client)
    assert isinstance(result, ImprovementPlan)
    assert len(result.actions) == 1
    assert result.actions[0].action_id == "A1"
    assert result.total_expected_score_delta == 15.0

def test_planner_retries_on_malformed_json(profile, scorecard, mock_client):
    mock_client.generate.side_effect = ["not json at all.", VALID_PLAN_JSON]
    result = generate_plan(profile, scorecard, mock_client)
    assert isinstance(result, ImprovementPlan)
    assert mock_client.generate.call_count == 2

def test_planner_returns_fallback_on_total_failure(profile, scorecard, mock_client):
    mock_client.generate.side_effect = Exception("API down")
    result = generate_plan(profile, scorecard, mock_client)
    assert isinstance(result, ImprovementPlan)
    assert len(result.actions) > 0

def test_planner_contradiction_check_unknown_dimension(scorecard):
    data = json.loads(VALID_PLAN_JSON)
    data["actions"][0]["dimension_affected"] = "Nonexistent Dimension"
    with pytest.raises(ValueError, match="Unknown dimension_affected"):
        _validate_and_build(data, scorecard)

def test_planner_contradiction_check_unchangeable_dimension(scorecard):
    data = json.loads(VALID_PLAN_JSON)
    data["actions"][0]["dimension_affected"] = "Business Vintage"
    with pytest.raises(ValueError, match="unchangeable dimension"):
        _validate_and_build(data, scorecard)

def test_parse_response_strips_markdown_fences():
    raw = "```json\n{\"actions\": []}\n```"
    result = _parse_response(raw)
    assert result == {"actions": []}

def test_parse_response_raises_on_invalid_json():
    with pytest.raises(ValueError, match="JSON parse failed"):
        _parse_response("not json")

def test_planner_fallback_skips_unchangeable_dimensions(scorecard):
    result = plan_fallback(scorecard)
    dim_names = [a.dimension_affected for a in result.actions]
    assert "Business Vintage" not in dim_names
    assert "Sectoral Risk" not in dim_names

def test_planner_fallback_is_valid_improvement_plan(scorecard):
    result = plan_fallback(scorecard)
    assert isinstance(result, ImprovementPlan)
    assert all(isinstance(a, Action) for a in result.actions)
    assert result.estimated_timeline_weeks > 0
