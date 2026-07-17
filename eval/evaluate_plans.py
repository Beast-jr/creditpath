import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.scorecard.engine import score_business
from core.schema import BusinessProfile
from core.llm.client import GeminiClient
from core.llm.planner import generate_plan

UNCHANGEABLE = {'Business Vintage', 'Sectoral Risk'}


def load_ground_truth(path='eval/improvement_plan_ground_truth.json'):
    with open(path) as f:
        return json.load(f)


def load_personas(path='tests/fixtures/golden_personas.json'):
    with open(path) as f:
        return json.load(f)


def evaluate_plan(plan, gt):
    results = {}

    # 1. action_coverage: at least one action targets an expected dimension
    plan_dims = {a.dimension_affected for a in plan.actions}
    expected = set(gt['expected_dimensions'])
    coverage = len(plan_dims & expected) / max(len(expected), 1)
    results['action_coverage'] = round(coverage, 4)

    # 2. no_hallucination: no action targets a forbidden dimension
    forbidden = set(gt['forbidden_dimensions'])
    violations = plan_dims & forbidden
    results['no_hallucination'] = len(violations) == 0
    results['hallucination_violations'] = list(violations)

    # 3. timeline_realism: all actions have timeline >= 2, total <= max
    timeline_ok = all(a.timeline_weeks >= 2 for a in plan.actions)
    timeline_ok = timeline_ok and plan.estimated_timeline_weeks <= gt['max_timeline_weeks']
    results['timeline_realism'] = timeline_ok

    # 4. priority_alignment: highest delta action targets a weak/expected dimension
    if plan.actions:
        top_action = max(plan.actions, key=lambda a: a.expected_score_delta)
        results['priority_alignment'] = top_action.dimension_affected in expected
    else:
        results['priority_alignment'] = False

    # 5. min_actions met
    results['min_actions_met'] = len(plan.actions) >= gt['min_actions']

    # 6. delta_cap: total delta <= max
    results['delta_cap_respected'] = plan.total_expected_score_delta <= gt['max_total_delta']

    # overall pass: all checks pass
    results['passed'] = all([
        results['action_coverage'] > 0,
        results['no_hallucination'],
        results['timeline_realism'],
        results['priority_alignment'],
        results['min_actions_met'],
        results['delta_cap_respected'],
    ])

    return results


if __name__ == '__main__':
    ground_truth = load_ground_truth()
    personas = load_personas()
    client = GeminiClient()

    print('Evaluating improvement plans for 20 personas...')
    print('(Uses cache — only calls API on first run)\n')

    all_results = []
    passed = 0

    for gt in ground_truth:
        i = gt['persona_index']
        p = personas[i]
        profile = BusinessProfile(**{k: v for k, v in p.items() if k != 'expected_tier'})
        scorecard = score_business(profile)
        plan = generate_plan(profile, scorecard, client)
        result = evaluate_plan(plan, gt)
        result['persona_index'] = i
        result['business_name'] = gt['business_name']
        result['tier'] = gt['tier']
        result['plan_actions'] = len(plan.actions)
        result['plan_total_delta'] = plan.total_expected_score_delta
        result['plan_dims'] = list({a.dimension_affected for a in plan.actions})
        all_results.append(result)
        status = 'PASS' if result['passed'] else 'FAIL'
        if result['passed']:
            passed += 1
        print(f"  [{status}] {gt['business_name']} ({gt['tier']}) — {len(plan.actions)} actions, delta={plan.total_expected_score_delta}")
        if not result['no_hallucination']:
            print(f"         HALLUCINATION: {result['hallucination_violations']}")
        if not result['timeline_realism']:
            print(f"         TIMELINE: estimated={plan.estimated_timeline_weeks}wk max={gt['max_timeline_weeks']}wk")

    print(f'\n=== SUMMARY ===')
    print(f'  Passed: {passed}/20')
    print(f'  action_coverage avg: {round(sum(r["action_coverage"] for r in all_results)/20, 4)}')
    print(f'  no_hallucination: {sum(1 for r in all_results if r["no_hallucination"])}/20')
    print(f'  timeline_realism: {sum(1 for r in all_results if r["timeline_realism"])}/20')
    print(f'  priority_alignment: {sum(1 for r in all_results if r["priority_alignment"])}/20')
    print(f'  delta_cap_respected: {sum(1 for r in all_results if r["delta_cap_respected"])}/20')

    Path('eval/results').mkdir(exist_ok=True)
    with open('eval/results/plan_eval_results.json', 'w') as f:
        json.dump(all_results, f, indent=2)
    print('\nResults saved to eval/results/plan_eval_results.json')
