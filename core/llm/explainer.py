"""LLM Call 1 — Assessment explainer.
Wraps ASSESSMENT_EXPLANATION_PROMPT with retry-on-refusal and a template fallback.
Never raises — always returns a string the pipeline can use.
"""
import hashlib
from core.llm.client import GeminiClient
from core.llm.prompts import ASSESSMENT_EXPLANATION_PROMPT, REFUSAL_PHRASES
from core.schema import ScorecardResult, BusinessProfile

MIN_RESPONSE_LENGTH = 50
MAX_RETRIES = 2


def _cache_key_inputs(profile: BusinessProfile, scorecard: ScorecardResult) -> str:
    raw = (
        f"{profile.business_name}|{profile.sector}|{profile.city}"
        f"|{profile.loan_amount_sought_inr}|{scorecard.weighted_score}"
        f"|{scorecard.tier}|{'|'.join(scorecard.weakest_dimensions)}"
    )
    return hashlib.sha256(raw.encode()).hexdigest()


def _is_refusal(text: str) -> bool:
    lower = text.lower()
    return any(phrase in lower for phrase in REFUSAL_PHRASES)


def _template_fallback(profile: BusinessProfile, scorecard: ScorecardResult) -> str:
    w1 = scorecard.weakest_dimensions[0] if scorecard.weakest_dimensions else "cash flow"
    tier_map = {
        "LOAN_READY": "ready for a loan",
        "NEARLY_READY": "nearly ready for a loan",
        "NEEDS_WORK": "not yet ready for a loan",
        "NOT_READY": "not ready for a loan at this time",
    }
    tier_text = tier_map.get(scorecard.tier, "at an early stage")
    return (
        f"{profile.business_name} scored {scorecard.weighted_score}/100 and is {tier_text}. "
        f"The weakest area is {w1}, which is bringing the overall score down. "
        f"Improving this area will have the biggest impact on loan eligibility. "
        f"Focus on {w1.lower()} as the first priority before applying."
    )


def generate_explanation(
    profile: BusinessProfile,
    scorecard: ScorecardResult,
    client: GeminiClient,
) -> str:
    weakest = scorecard.weakest_dimensions
    w1 = weakest[0] if len(weakest) > 0 else "Cash Flow Consistency"
    w2 = weakest[1] if len(weakest) > 1 else "GST Filing Regularity"
    reason_map = {d.dimension_name: d.reason for d in scorecard.dimension_scores}
    w1_reason = reason_map.get(w1, "score is low")
    w2_reason = reason_map.get(w2, "score is low")
    prompt = ASSESSMENT_EXPLANATION_PROMPT.format(
        business_name=profile.business_name,
        sector=profile.sector,
        city=profile.city,
        loan_amount=profile.loan_amount_sought_inr,
        score=scorecard.weighted_score,
        tier=scorecard.tier,
        weakest_1_name=w1,
        weakest_1_reason=w1_reason,
        weakest_2_name=w2,
        weakest_2_reason=w2_reason,
    )
    for attempt in range(MAX_RETRIES):
        try:
            response = client.generate(prompt, timeout=30)
            if len(response.strip()) < MIN_RESPONSE_LENGTH or _is_refusal(response):
                continue
            return response.strip()
        except Exception:
            continue
    return _template_fallback(profile, scorecard)
