"""Iteration test for IMPROVEMENT_PLAN_PROMPT. Run with PYTHONPATH=. python scripts/test_improvement_planner.py"""
import json
from core.scorecard.engine import score_business
from core.schema import BusinessProfile
from core.llm.client import GeminiClient
from core.llm.prompts import IMPROVEMENT_PLAN_PROMPT

client = GeminiClient()
personas = json.load(open('tests/fixtures/golden_personas.json'))

PERSONA_INDEX = 5  # change to 0, 1 etc to test different personas

p = personas[PERSONA_INDEX]
profile = BusinessProfile(**{k: v for k, v in p.items() if k != 'expected_tier'})
sc = score_business(profile)

lines = []
for d in sc.dimension_scores:
    lines.append(f"  {d.dimension_name}: {d.score}/100 ({d.label}) — {d.reason}")
dimension_details = "\n".join(lines)

prompt = IMPROVEMENT_PLAN_PROMPT.format(
    business_name=profile.business_name,
    sector=profile.sector,
    city=profile.city,
    loan_amount=profile.loan_amount_sought_inr,
    score=sc.weighted_score,
    tier=sc.tier,
    dimension_details=dimension_details,
)

print(f"=== PERSONA {PERSONA_INDEX}: {profile.business_name} ===")
print(f"Tier: {sc.tier} | Score: {sc.weighted_score}")
print(f"Weakest: {sc.weakest_dimensions}")
print(f"Prompt length: {len(prompt)} chars")
print("\nCalling Gemini...")

response = client.generate(prompt, timeout=60)

print("\n--- RAW RESPONSE ---")
print(response)

print("\n--- PARSE CHECK ---")
try:
    clean = response.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    parsed = json.loads(clean)
    print(f"OK — {len(parsed.get('actions', []))} actions, {len(parsed.get('milestones', []))} milestones")
    print(f"Total delta: {parsed.get('total_expected_score_delta')}, Timeline: {parsed.get('estimated_timeline_weeks')} weeks")
    for a in parsed.get('actions', []):
        print(f"  {a['action_id']}: {a['dimension_affected']} +{a['expected_score_delta']}pts, {a['timeline_weeks']}wk, {a['effort_level']}, {len(a['specific_steps'])} steps")
except json.JSONDecodeError as e:
    print(f"JSON PARSE FAILED: {e}")
