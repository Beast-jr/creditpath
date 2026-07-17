"""API tests using FastAPI TestClient. All heavy components mocked."""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from core.schema import (
    BusinessProfile, ScorecardResult, DimensionScore,
    ImprovementPlan, Action, Milestone, RecommendationResult,
    ClusterAssignment, AssessmentOutput, SchemeDocument, SchemeMatch,
)

SAMPLE_REQUEST = {
    "business_name": "Kumar Auto Spares",
    "owner_name": "Ramesh Kumar",
    "sector": "Automotive",
    "city": "Hubli",
    "state": "Karnataka",
    "geographic_tier": 2,
    "monthly_revenue_inr": 150000,
    "revenue_consistency_pct": 72.0,
    "existing_emi_inr": 18000,
    "gst_filing_rate_pct": 78.0,
    "vintage_months": 30,
    "has_collateral": True,
    "collateral_value_inr": 500000,
    "loan_amount_sought_inr": 800000,
}

SAMPLE_SCHEME = SchemeDocument(
    scheme_id="pmmy_mudra",
    name="PMMY Mudra",
    administered_by="Ministry of Finance",
    scheme_type="loan",
    target_segments=["micro"],
    loan_range_min=0,
    loan_range_max=1000000,
    interest_rate_min=0.0,
    interest_rate_max=0.0,
    collateral_required=False,
    eligibility_vintage_months_min=0,
    eligibility_gst_required=False,
    eligibility_sectors_included=[],
    eligibility_sectors_excluded=[],
    eligibility_geographic_restriction=None,
    retrieval_text="Mudra loan for micro enterprises",
    official_url="https://www.mudra.org.in",
    last_verified_date="2024-01-01",
)

SAMPLE_SCORECARD = ScorecardResult(
    dimension_scores=[
        DimensionScore(dimension_name="Cash Flow Consistency", score=70.0, label="ADEQUATE", reason="Revenue consistency at 72%"),
        DimensionScore(dimension_name="Debt Service Coverage Ratio", score=45.0, label="WEAK", reason="EMI burden high"),
        DimensionScore(dimension_name="GST Filing Regularity", score=70.0, label="ADEQUATE", reason="GST rate 78%"),
        DimensionScore(dimension_name="Business Vintage", score=45.0, label="WEAK", reason="30 months"),
        DimensionScore(dimension_name="Sectoral Risk", score=65.0, label="ADEQUATE", reason="Medium risk"),
        DimensionScore(dimension_name="Collateral Availability", score=90.0, label="STRONG", reason="Covers loan"),
    ],
    weighted_score=53.25,
    tier="NEARLY_READY",
    weakest_dimensions=["Debt Service Coverage Ratio", "Business Vintage"],
    execution_time_ms=12,
)

SAMPLE_PLAN = ImprovementPlan(
    actions=[Action(
        action_id="A1",
        description="Collect overdue payments.",
        dimension_affected="Debt Service Coverage Ratio",
        expected_score_delta=15.0,
        timeline_weeks=6,
        effort_level="MEDIUM",
        specific_steps=["List overdue customers", "Call each one"],
    )],
    dependencies=[],
    milestones=[Milestone(title="Initial boost", target_week=6, action_ids=["A1"])],
    total_expected_score_delta=15.0,
    estimated_timeline_weeks=6,
)

SAMPLE_RECOMMENDATIONS = RecommendationResult(
    matches=[SchemeMatch(
        scheme=SAMPLE_SCHEME,
        match_score=0.75,
        eligibility_explanation="Good match for sector and loan amount.",
    )],
    total_found=5,
)

SAMPLE_CLUSTER = ClusterAssignment(
    cluster_id=1,
    label="Growth-Stage Small Businesses",
    centroid_distance=0.42,
    peer_description="Similar businesses with moderate revenue.",
)

SAMPLE_OUTPUT = AssessmentOutput(
    profile=BusinessProfile(**SAMPLE_REQUEST),
    scorecard=SAMPLE_SCORECARD,
    explanation="Nearly ready for a loan.",
    improvement_plan=SAMPLE_PLAN,
    recommendations=SAMPLE_RECOMMENDATIONS,
    cluster=SAMPLE_CLUSTER,
)


@pytest.fixture
def client():
    with patch("api.main.AssessmentPipeline") as MockPipeline, \
         patch("api.main.RecommendationEngine") as MockEngine, \
         patch("api.routes.whatif.score_business", return_value=SAMPLE_SCORECARD):
        MockPipeline.return_value.assess.return_value = SAMPLE_OUTPUT
        MockEngine.return_value.recommend.return_value = SAMPLE_RECOMMENDATIONS
        from api.main import app
        with TestClient(app) as c:
            yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_assess_happy_path(client):
    r = client.post("/assess", json=SAMPLE_REQUEST)
    assert r.status_code == 200
    data = r.json()
    assert "scorecard" in data
    assert "explanation" in data
    assert "improvement_plan" in data
    assert "recommendations" in data
    assert "cluster" in data


def test_assess_scorecard_fields(client):
    r = client.post("/assess", json=SAMPLE_REQUEST)
    sc = r.json()["scorecard"]
    assert sc["weighted_score"] == 53.25
    assert sc["tier"] == "NEARLY_READY"
    assert len(sc["dimension_scores"]) == 6


def test_assess_improvement_plan_fields(client):
    r = client.post("/assess", json=SAMPLE_REQUEST)
    plan = r.json()["improvement_plan"]
    assert len(plan["actions"]) == 1
    assert plan["actions"][0]["action_id"] == "A1"
    assert plan["total_expected_score_delta"] == 15.0


def test_assess_recommendations_fields(client):
    r = client.post("/assess", json=SAMPLE_REQUEST)
    recs = r.json()["recommendations"]
    assert recs["total_found"] == 5
    assert recs["matches"][0]["scheme_id"] == "pmmy_mudra"


def test_assess_cluster_fields(client):
    r = client.post("/assess", json=SAMPLE_REQUEST)
    cluster = r.json()["cluster"]
    assert cluster["cluster_id"] == 1
    assert cluster["label"] == "Growth-Stage Small Businesses"


def test_assess_validation_error(client):
    bad = {**SAMPLE_REQUEST, "monthly_revenue_inr": -1000}
    r = client.post("/assess", json=bad)
    assert r.status_code == 422


def test_assess_missing_field(client):
    bad = {k: v for k, v in SAMPLE_REQUEST.items() if k != "business_name"}
    r = client.post("/assess", json=bad)
    assert r.status_code == 422


def test_recommend_happy_path(client):
    r = client.post("/recommend", json=SAMPLE_REQUEST)
    assert r.status_code == 200
    data = r.json()
    assert "matches" in data
    assert "total_found" in data
    assert data["matches"][0]["scheme_id"] == "pmmy_mudra"


def test_recommend_validation_error(client):
    bad = {**SAMPLE_REQUEST, "loan_amount_sought_inr": 0}
    r = client.post("/recommend", json=bad)
    assert r.status_code == 422


def test_whatif_happy_path(client):
    r = client.post("/whatif", json=SAMPLE_REQUEST)
    assert r.status_code == 200
    data = r.json()
    assert "scorecard" in data
    assert "recommendations" in data
    assert "explanation" not in data
    assert "improvement_plan" not in data


def test_whatif_no_llm_fields(client):
    r = client.post("/whatif", json=SAMPLE_REQUEST)
    data = r.json()
    assert "explanation" not in data
    assert "cluster" not in data


def test_whatif_validation_error(client):
    bad = {**SAMPLE_REQUEST, "geographic_tier": 5}
    r = client.post("/whatif", json=bad)
    assert r.status_code == 422
