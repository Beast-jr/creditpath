from fastapi import APIRouter, Depends, HTTPException
from api.schemas import BusinessProfileRequest, RecommendationResponse, SchemeMatchResponse
from api.dependencies import get_recommendation_engine
from core.recommendation.engine import RecommendationEngine
from core.schema import BusinessProfile

router = APIRouter(prefix="/recommend", tags=["recommendation"])


@router.post("", response_model=RecommendationResponse)
async def recommend(
    request: BusinessProfileRequest,
    engine: RecommendationEngine = Depends(get_recommendation_engine),
):
    try:
        profile = BusinessProfile(**request.model_dump())
        result = engine.recommend(profile, top_k=5)
        return RecommendationResponse(
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
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
