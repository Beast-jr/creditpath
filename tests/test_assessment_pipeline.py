"""Tests for core/observability.py and core/assessment_pipeline.py.
Pipeline tests mock all heavy components — no real API calls, no ChromaDB needed.
"""
import uuid
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from core.schema import (
    BusinessProfile, ScorecardResult, DimensionScore,
    ImprovementPlan, Action, Milestone, RecommendationResult,
    ClusterAssignment, AssessmentOutput, AssessmentEvent,
)
from core.observability import ObservabilityLogger
from core.assessment_pipeline import AssessmentPipeline


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

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

@pytest.fixture
def improvement_plan():
    return ImprovementPlan(
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

@pytest.fixture
def cluster():
    return ClusterAssignment(
        cluster_id=1,
        label="Growth-Stage Small Businesses",
        centroid_distance=0.42,
        peer_description="Similar businesses have 2-4 years vintage and moderate revenue.",
    )

@pytest.fixture
def recommendations():
    return RecommendationResult(matches=[], total_found=0)

@pytest.fixture
def tmp_logger(tmp_path):
    return ObservabilityLogger(db_path=tmp_path / "test.db")

@pytest.fixture
def sample_event(profile, scorecard, improvement_plan, cluster, recommendations):
    return AssessmentEvent(
        event_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),
        profile=profile,
        scorecard_result=scorecard,
        explanation="Nearly ready for a loan.",
        improvement_plan=improvement_plan,
        recommendation_result=recommendations,
        cluster_assignment=cluster,
        scorecard_latency_ms=10,
        llm_explain_latency_ms=200,
        llm_plan_latency_ms=400,
        retrieval_latency_ms=50,
        total_latency_ms=660,
    )


# ---------------------------------------------------------------------------
# ObservabilityLogger tests
# ---------------------------------------------------------------------------

def test_logger_creates_db_file(tmp_path):
    db = tmp_path / "test.db"
    ObservabilityLogger(db_path=db)
    assert db.exists()

def test_logger_log_and_retrieve(tmp_logger, sample_event):
    tmp_logger.log_assessment(sample_event)
    rows = tmp_logger.get_recent_assessments(n=5)
    assert len(rows) == 1
    assert rows[0]["business_name"] == "Kumar Auto Spares"
    assert rows[0]["tier"] == "NEARLY_READY"
    assert rows[0]["weighted_score"] == 53.25
    assert rows[0]["total_latency_ms"] == 660

def test_logger_payload_fields(tmp_logger, sample_event):
    tmp_logger.log_assessment(sample_event)
    rows = tmp_logger.get_recent_assessments(n=1)
    assert rows[0]["plan_action_count"] == 1
    assert rows[0]["cluster_id"] == 1
    assert rows[0]["explanation_length"] > 0

def test_logger_get_recent_returns_most_recent_first(tmp_logger, scorecard, improvement_plan, cluster, recommendations):
    for name in ["First", "Second", "Third"]:
        p = BusinessProfile(
            business_name=name, owner_name="X", sector="Retail",
            city="Delhi", state="Delhi", geographic_tier=1,
            monthly_revenue_inr=100000, revenue_consistency_pct=80.0,
            existing_emi_inr=5000, gst_filing_rate_pct=90.0,
            vintage_months=24, has_collateral=False,
            collateral_value_inr=0, loan_amount_sought_inr=200000,
        )
        event = AssessmentEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            profile=p,
            scorecard_result=scorecard,
            explanation="Test.",
            improvement_plan=improvement_plan,
            recommendation_result=recommendations,
            cluster_assignment=cluster,
            scorecard_latency_ms=10,
            llm_explain_latency_ms=200,
            llm_plan_latency_ms=400,
            retrieval_latency_ms=50,
            total_latency_ms=660,
        )
        tmp_logger.log_assessment(event)
    rows = tmp_logger.get_recent_assessments(n=3)
    assert rows[0]["business_name"] == "Third"

def test_logger_swallows_errors_silently(tmp_path):
    logger = ObservabilityLogger(db_path=tmp_path / "test.db")
    logger.log_assessment(None)

def test_logger_get_recent_returns_empty_when_no_rows(tmp_logger):
    result = tmp_logger.get_recent_assessments()
    assert result == []

def test_logger_respects_n_limit(tmp_logger, sample_event):
    for _ in range(5):
        import uuid as u
        e = AssessmentEvent(
            event_id=str(u.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            profile=sample_event.profile,
            scorecard_result=sample_event.scorecard_result,
            explanation="Test.",
            improvement_plan=sample_event.improvement_plan,
            recommendation_result=sample_event.recommendation_result,
            cluster_assignment=sample_event.cluster_assignment,
            scorecard_latency_ms=10,
            llm_explain_latency_ms=200,
            llm_plan_latency_ms=400,
            retrieval_latency_ms=50,
            total_latency_ms=660,
        )
        tmp_logger.log_assessment(e)
    rows = tmp_logger.get_recent_assessments(n=3)
    assert len(rows) == 3


# ---------------------------------------------------------------------------
# AssessmentPipeline tests
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_pipeline(scorecard, improvement_plan, cluster, recommendations):
    with patch("core.assessment_pipeline.RecommendationEngine") as MockRec, \
         patch("core.assessment_pipeline.ProfileClusterer") as MockCluster, \
         patch("core.assessment_pipeline.GeminiClient"), \
         patch("core.assessment_pipeline.ObservabilityLogger"), \
         patch("core.assessment_pipeline.score_business", return_value=scorecard), \
         patch("core.assessment_pipeline.generate_explanation", return_value="Nearly ready for a loan."), \
         patch("core.assessment_pipeline.generate_plan", return_value=improvement_plan):
        MockRec.return_value.recommend.return_value = recommendations
        MockCluster.return_value.assign.return_value = cluster
        pipeline = AssessmentPipeline()
        yield pipeline


def test_pipeline_returns_assessment_output(mock_pipeline, profile):
    result = mock_pipeline.assess(profile)
    assert isinstance(result, AssessmentOutput)

def test_pipeline_output_profile_matches(mock_pipeline, profile):
    result = mock_pipeline.assess(profile)
    assert result.profile == profile

def test_pipeline_output_has_scorecard(mock_pipeline, profile):
    result = mock_pipeline.assess(profile)
    assert result.scorecard is not None
    assert result.scorecard.weighted_score == 53.25

def test_pipeline_output_explanation_is_string(mock_pipeline, profile):
    result = mock_pipeline.assess(profile)
    assert isinstance(result.explanation, str)
    assert len(result.explanation) > 0

def test_pipeline_output_has_improvement_plan(mock_pipeline, profile):
    result = mock_pipeline.assess(profile)
    assert len(result.improvement_plan.actions) > 0

def test_pipeline_output_has_cluster(mock_pipeline, profile):
    result = mock_pipeline.assess(profile)
    assert result.cluster is not None
    assert result.cluster.cluster_id == 1

def test_pipeline_raises_on_invalid_profile(mock_pipeline):
    with pytest.raises((ValueError, TypeError, AttributeError)):
        mock_pipeline.assess(None)

def test_pipeline_calls_logger(scorecard, improvement_plan, cluster, recommendations, profile):
    with patch("core.assessment_pipeline.RecommendationEngine") as MockRec, \
         patch("core.assessment_pipeline.ProfileClusterer") as MockCluster, \
         patch("core.assessment_pipeline.GeminiClient"), \
         patch("core.assessment_pipeline.ObservabilityLogger") as MockLogger, \
         patch("core.assessment_pipeline.score_business", return_value=scorecard), \
         patch("core.assessment_pipeline.generate_explanation", return_value="Nearly ready."), \
         patch("core.assessment_pipeline.generate_plan", return_value=improvement_plan):
        MockRec.return_value.recommend.return_value = recommendations
        MockCluster.return_value.assign.return_value = cluster
        pipeline = AssessmentPipeline()
        pipeline.assess(profile)
        assert MockLogger.return_value.log_assessment.call_count == 1
