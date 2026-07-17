from fastapi import APIRouter, Depends, HTTPException
from api.schemas import (
    BusinessProfileRequest, AssessmentResponse,
    ScorecardResponse, DimensionScoreResponse,
    ImprovementPlanResponse, ActionResponse, ActionDependencyResponse, MilestoneResponse,
    RecommendationResponse, SchemeMatchResponse, ClusterResponse,
)
from api.dependencies import get_assessment_pipeline
from core.assessment_pipeline import AssessmentPipeline
from core.schema import BusinessProfile

router = APIRouter(prefix="/assess", tags=["assessment"])


def _build_response(output) -> AssessmentResponse:
    scorecard = ScorecardResponse(
        dimension_scores=[
            DimensionScoreResponse(
                dimension_name=d.dimension_name,
                score=d.score,
                label=d.label,
                reason=d.reason,
            )
            for d in output.scorecard.dimension_scores
        ],
        weighted_score=output.scorecard.weighted_score,
        tier=output.scorecard.tier,
        weakest_dimensions=output.scorecard.weakest_dimensions,
        execution_time_ms=output.scorecard.execution_time_ms,
    )
    plan = ImprovementPlanResponse(
        actions=[
            ActionResponse(
                action_id=a.action_id,
                description=a.description,
                dimension_affected=a.dimension_affected,
                expected_score_delta=a.expected_score_delta,
                timeline_weeks=a.timeline_weeks,
                effort_level=a.effort_level,
                specific_steps=a.specific_steps,
            )
            for a in output.improvement_plan.actions
        ],
        dependencies=[
            ActionDependencyResponse(
                action_id=d.action_id,
                depends_on_action_id=d.depends_on_action_id,
                reason=d.reason,
            )
            for d in output.improvement_plan.dependencies
        ],
        milestones=[
            MilestoneResponse(
                title=m.title,
                target_week=m.target_week,
                action_ids=m.action_ids,
            )
            for m in output.improvement_plan.milestones
        ],
        total_expected_score_delta=output.improvement_plan.total_expected_score_delta,
        estimated_timeline_weeks=output.improvement_plan.estimated_timeline_weeks,
    )
    recommendations = RecommendationResponse(
        matches=[
            SchemeMatchResponse(
                scheme_id=m.scheme.scheme_id,
                scheme_name=m.scheme.name,
                match_score=m.match_score,
                eligibility_explanation=m.eligibility_explanation,
                loan_range_min=m.scheme.loan_range_min,
                loan_range_max=m.scheme.loan_range_max,
                interest_rate_min=m.scheme.interest_rate_min,
                interest_rate_max=m.scheme.interest_rate_max,
                official_url=m.scheme.official_url,
            )
            for m in output.recommendations.matches
        ],
        total_found=output.recommendations.total_found,
    )
    cluster = ClusterResponse(
        cluster_id=output.cluster.cluster_id,
        label=output.cluster.label,
        centroid_distance=output.cluster.centroid_distance,
        peer_description=output.cluster.peer_description,
    )
    return AssessmentResponse(
        scorecard=scorecard,
        explanation=output.explanation,
        improvement_plan=plan,
        recommendations=recommendations,
        cluster=cluster,
    )


@router.post("", response_model=AssessmentResponse)
async def assess(
    request: BusinessProfileRequest,
    pipeline: AssessmentPipeline = Depends(get_assessment_pipeline),
):
    try:
        profile = BusinessProfile(**request.model_dump())
        output = pipeline.assess(profile)
        return _build_response(output)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
