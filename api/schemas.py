from pydantic import BaseModel, Field, field_validator


class BusinessProfileRequest(BaseModel):
    business_name: str = Field(..., min_length=1, max_length=100)
    owner_name: str = Field(..., min_length=1, max_length=100)
    sector: str = Field(..., min_length=1, max_length=50)
    city: str = Field(..., min_length=1, max_length=50)
    state: str = Field(..., min_length=1, max_length=50)
    geographic_tier: int = Field(..., ge=1, le=3)
    monthly_revenue_inr: float = Field(..., gt=0)
    revenue_consistency_pct: float = Field(..., ge=0, le=100)
    existing_emi_inr: float = Field(..., ge=0)
    gst_filing_rate_pct: float = Field(..., ge=0, le=100)
    vintage_months: int = Field(..., ge=0)
    has_collateral: bool
    collateral_value_inr: float = Field(..., ge=0)
    loan_amount_sought_inr: float = Field(..., gt=0)

    @field_validator('monthly_revenue_inr', 'loan_amount_sought_inr')
    @classmethod
    def must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('must be positive')
        return v


class DimensionScoreResponse(BaseModel):
    dimension_name: str
    score: float
    label: str
    reason: str


class ScorecardResponse(BaseModel):
    dimension_scores: list[DimensionScoreResponse]
    weighted_score: float
    tier: str
    weakest_dimensions: list[str]
    execution_time_ms: int


class ActionResponse(BaseModel):
    action_id: str
    description: str
    dimension_affected: str
    expected_score_delta: float
    timeline_weeks: int
    effort_level: str
    specific_steps: list[str]


class ActionDependencyResponse(BaseModel):
    action_id: str
    depends_on_action_id: str
    reason: str


class MilestoneResponse(BaseModel):
    title: str
    target_week: int
    action_ids: list[str]


class ImprovementPlanResponse(BaseModel):
    actions: list[ActionResponse]
    dependencies: list[ActionDependencyResponse]
    milestones: list[MilestoneResponse]
    total_expected_score_delta: float
    estimated_timeline_weeks: int


class SchemeMatchResponse(BaseModel):
    scheme_id: str
    scheme_name: str
    match_score: float
    eligibility_explanation: str
    loan_range_min: int
    loan_range_max: int
    interest_rate_min: float
    interest_rate_max: float
    official_url: str


class RecommendationResponse(BaseModel):
    matches: list[SchemeMatchResponse]
    total_found: int


class ClusterResponse(BaseModel):
    cluster_id: int
    label: str
    centroid_distance: float
    peer_description: str


class AssessmentResponse(BaseModel):
    scorecard: ScorecardResponse
    explanation: str
    improvement_plan: ImprovementPlanResponse
    recommendations: RecommendationResponse
    cluster: ClusterResponse


class WhatIfResponse(BaseModel):
    scorecard: ScorecardResponse
    recommendations: RecommendationResponse


class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"
