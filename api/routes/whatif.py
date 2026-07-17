from fastapi import APIRouter, Depends, HTTPException
from api.schemas import (
    BusinessProfileRequest, WhatIfResponse,
    ScorecardResponse, DimensionScoreResponse,
    RecommendationResponse, SchemeMatchResponse,
)
from api.dependencies import get_recommendation_engine
from core.recommendation.engine import RecommendationEngine
from core.scorecard.engine import score_business
from core.schema import BusinessProfile

router = APIRouter(prefix="/whatif", tags=["whatif"])


@router.post("", response_model=WhatIfResponse)
async def whatif(
    request: BusinessProfileRequest,
    engine: RecommendationEngine = Depends(get_recommendation_engine),
):
    try:
        profile = BusinessProfile(**request.model_dump())
        scorecard = score_business(profile)
        result = engine.recommend(profile, top_k=5)
        return WhatIfResponse(
            scorecard=ScorecardResponse(
                dimension_scores=[
                    DimensionScoreResponse(
                        dimension_name=d.dimension_name,
                        score=d.score,
                        label=d.label,
                        reason=d.reason,
                    )
                    for d in scorecard.dimension_scores
                ],
                weighted_score=scorecard.weighted_score,
                tier=scorecard.tier,
                weakest_dimensions=scorecard.weakest_dimensions,
                execution_time_ms=scorecard.execution_time_ms,
            ),
            recommendations=RecommendationResponse(
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
                    for m in result.matches
                ],
                total_found=result.total_found,
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
