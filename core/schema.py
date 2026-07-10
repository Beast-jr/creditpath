"""Single source of truth for every data type in CreditPath. Imported everywhere."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class BusinessProfile:
    """All raw user inputs from the assessment form."""
    business_name: str
    owner_name: str
    sector: str                      # e.g. "textile", "retail", "manufacturing"
    city: str
    state: str
    geographic_tier: int             # 1, 2, or 3 (metro / tier-2 / tier-3)
    monthly_revenue_inr: float       # average monthly revenue, INR
    revenue_consistency_pct: float   # 0–100, month-to-month stability
    existing_emi_inr: float          # total existing monthly EMIs, INR
    gst_filing_rate_pct: float       # 0–100, % returns filed on time
    vintage_months: int              # months in operation
    has_collateral: bool
    collateral_value_inr: float      # 0.0 if no collateral
    loan_amount_sought_inr: float


@dataclass
class DimensionScore:
    """One scored dimension of the scorecard."""
    dimension_name: str
    score: float                     # 0–100
    label: str                       # STRONG / ADEQUATE / WEAK / CRITICAL
    reason: str                      # specific, human-readable justification


@dataclass
class ScorecardResult:
    """Full scorecard output across all six dimensions."""
    dimension_scores: List[DimensionScore]
    weighted_score: float            # 0–100
    tier: str                        # LOAN_READY / NEARLY_READY / NEEDS_WORK / NOT_READY
    weakest_dimensions: List[str]    # dimension names, worst first
    execution_time_ms: float


@dataclass
class SchemeDocument:
    """One government/SIDBI financing scheme with all metadata."""
    scheme_id: str
    name: str
    administered_by: str
    scheme_type: str
    target_segments: List[str]
    loan_range_min: float
    loan_range_max: float
    interest_rate_min: float
    interest_rate_max: float
    collateral_required: bool
    eligibility_vintage_months_min: int
    eligibility_gst_required: bool
    eligibility_sectors_included: List[str]   # empty = all sectors
    eligibility_sectors_excluded: List[str]
    eligibility_geographic_restriction: str   # "" = no restriction
    retrieval_text: str                       # text embedded for vector search
    official_url: str
    last_verified_date: str                   # ISO date, YYYY-MM-DD


@dataclass
class SchemeMatch:
    """A scheme retrieved for a profile, with its match score."""
    scheme: SchemeDocument
    match_score: float               # 0–1
    eligibility_explanation: str


@dataclass
class RecommendationResult:
    """Ranked schemes returned for a profile."""
    matches: List[SchemeMatch]
    total_found: int


@dataclass
class Action:
    """One concrete step in an improvement plan."""
    action_id: str
    description: str
    dimension_affected: str
    expected_score_delta: float      # projected weighted-score gain
    timeline_weeks: int
    effort_level: str                # LOW / MEDIUM / HIGH
    specific_steps: List[str]


@dataclass
class ActionDependency:
    """Declares that one action must precede another."""
    action_id: str
    depends_on_action_id: str
    reason: str


@dataclass
class Milestone:
    """A checkpoint grouping actions by target week."""
    title: str
    target_week: int
    action_ids: List[str]


@dataclass
class ImprovementPlan:
    """Structured plan produced by the LLM planner (Call 2)."""
    actions: List[Action]
    dependencies: List[ActionDependency]
    milestones: List[Milestone]
    total_expected_score_delta: float
    estimated_timeline_weeks: int


@dataclass
class ClusterAssignment:
    """Which peer cluster this profile belongs to (K-Means)."""
    cluster_id: int
    label: str
    centroid_distance: float
    peer_description: str


@dataclass
class AssessmentOutput:
    """Complete result returned to the frontend for one assessment."""
    profile: BusinessProfile
    scorecard: ScorecardResult
    explanation: str                 # LLM Call 1 output
    improvement_plan: ImprovementPlan
    recommendations: RecommendationResult
    cluster: ClusterAssignment


@dataclass
class AssessmentEvent:
    """Full observability log entry (inputs, outputs, latencies)."""
    event_id: str
    timestamp: str                   # ISO 8601
    profile: BusinessProfile
    scorecard_result: ScorecardResult
    explanation: str
    improvement_plan: ImprovementPlan
    recommendation_result: RecommendationResult
    cluster_assignment: ClusterAssignment
    scorecard_latency_ms: float
    llm_explain_latency_ms: float
    llm_plan_latency_ms: float
    retrieval_latency_ms: float
    total_latency_ms: float


def validate_business_profile(profile: BusinessProfile) -> None:
    """Raise ValueError with a specific message for any invalid input."""
    if profile.monthly_revenue_inr <= 0:
        raise ValueError("monthly_revenue_inr must be greater than 0")
    if not 0 <= profile.gst_filing_rate_pct <= 100:
        raise ValueError("gst_filing_rate_pct must be between 0 and 100")
    if not 0 <= profile.revenue_consistency_pct <= 100:
        raise ValueError("revenue_consistency_pct must be between 0 and 100")
    if profile.vintage_months < 0:
        raise ValueError("vintage_months must be 0 or greater")
    if profile.loan_amount_sought_inr <= 0:
        raise ValueError("loan_amount_sought_inr must be greater than 0")
    if profile.geographic_tier not in (1, 2, 3):
        raise ValueError("geographic_tier must be 1, 2, or 3")