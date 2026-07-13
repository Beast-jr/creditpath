"""LLM Call 2 — Improvement planner.
Wraps IMPROVEMENT_PLAN_PROMPT with JSON parsing, contradiction check,
retry on malformed JSON, and a template fallback.
Never raises — always returns an ImprovementPlan.
"""
import json
from core.llm.client import GeminiClient
from core.llm.prompts import IMPROVEMENT_PLAN_PROMPT
from core.schema import (
    ScorecardResult, BusinessProfile,
    ImprovementPlan, Action, ActionDependency, Milestone,
)

MAX_RETRIES = 2
UNCHANGEABLE_DIMENSIONS = {"Business Vintage", "Sectoral Risk"}


def _build_prompt(profile: BusinessProfile, scorecard: ScorecardResult) -> str:
    lines = []
    for d in scorecard.dimension_scores:
        lines.append(f"  {d.dimension_name}: {d.score}/100 ({d.label}) — {d.reason}")
    dimension_details = "\n".join(lines)
    return IMPROVEMENT_PLAN_PROMPT.format(
        business_name=profile.business_name,
        sector=profile.sector,
        city=profile.city,
        loan_amount=profile.loan_amount_sought_inr,
        score=scorecard.weighted_score,
        tier=scorecard.tier,
        dimension_details=dimension_details,
    )


def _parse_response(raw: str) -> dict:
    clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON parse failed: {e}")


def _validate_and_build(data: dict, scorecard: ScorecardResult) -> ImprovementPlan:
    valid_dimensions = {d.dimension_name for d in scorecard.dimension_scores}
    actions = []
    for a in data.get("actions", []):
        dim = a.get("dimension_affected", "")
        if dim not in valid_dimensions:
            raise ValueError(f"Unknown dimension_affected: {dim!r}")
        if dim in UNCHANGEABLE_DIMENSIONS:
            raise ValueError(f"Action targets unchangeable dimension: {dim!r}")
        actions.append(Action(
            action_id=a["action_id"],
            description=a["description"],
            dimension_affected=dim,
            expected_score_delta=float(a["expected_score_delta"]),
            timeline_weeks=int(a["timeline_weeks"]),
            effort_level=a["effort_level"],
            specific_steps=a["specific_steps"],
        ))
    dependencies = [
        ActionDependency(
            action_id=d["action_id"],
            depends_on_action_id=d["depends_on_action_id"],
            reason=d["reason"],
        )
        for d in data.get("dependencies", [])
    ]
    milestones = [
        Milestone(
            title=m["title"],
            target_week=int(m["target_week"]),
            action_ids=m["action_ids"],
        )
        for m in data.get("milestones", [])
    ]
    return ImprovementPlan(
        actions=actions,
        dependencies=dependencies,
        milestones=milestones,
        total_expected_score_delta=float(data.get("total_expected_score_delta", 0)),
        estimated_timeline_weeks=int(data.get("estimated_timeline_weeks", 0)),
    )


def _template_fallback(scorecard: ScorecardResult) -> ImprovementPlan:
    fixable = [
        d for d in scorecard.weakest_dimensions
        if d not in UNCHANGEABLE_DIMENSIONS
    ][:2]
    actions = []
    for i, dim in enumerate(fixable):
        actions.append(Action(
            action_id=f"A{i+1}",
            description=f"Take steps to improve your {dim} score.",
            dimension_affected=dim,
            expected_score_delta=10.0,
            timeline_weeks=8,
            effort_level="MEDIUM",
            specific_steps=[
                f"Review your current {dim.lower()} situation.",
                f"Identify the single most impactful change you can make.",
                "Track your progress weekly.",
            ],
        ))
    milestones = [
        Milestone(title="Improvement Plan", target_week=8, action_ids=[a.action_id for a in actions])
    ] if actions else []
    return ImprovementPlan(
        actions=actions,
        dependencies=[],
        milestones=milestones,
        total_expected_score_delta=sum(a.expected_score_delta for a in actions),
        estimated_timeline_weeks=8,
    )


def generate_plan(
    profile: BusinessProfile,
    scorecard: ScorecardResult,
    client: GeminiClient,
) -> ImprovementPlan:
    prompt = _build_prompt(profile, scorecard)
    for attempt in range(MAX_RETRIES):
        try:
            raw = client.generate(prompt, timeout=60)
            data = _parse_response(raw)
            return _validate_and_build(data, scorecard)
        except Exception:
            continue
    return _template_fallback(scorecard)
