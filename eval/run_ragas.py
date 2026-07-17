import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.recommendation.engine import RecommendationEngine
from core.schema import BusinessProfile


def load_ground_truth(path='eval/ground_truth.json'):
    with open(path) as f:
        return json.load(f)


def load_personas(path='tests/fixtures/golden_personas.json'):
    with open(path) as f:
        return json.load(f)


def evaluate(engine, ground_truth, personas):
    hits, precisions, reciprocal_ranks, absent_violations = [], [], [], []
    for entry in ground_truth:
        persona = personas[entry['persona_index']]
        profile = BusinessProfile(**{k: v for k, v in persona.items() if k != 'expected_tier'})
        result = engine.recommend(profile, top_k=5)
        retrieved_ids = [m.scheme.scheme_id for m in result.matches]
        expected = set(entry['expected_scheme_ids'])
        absent = set(entry['expected_absent_ids'])
        hit = any(sid in retrieved_ids for sid in expected)
        hits.append(1 if hit else 0)
        relevant_in_top5 = sum(1 for sid in retrieved_ids if sid in expected)
        precisions.append(relevant_in_top5 / len(retrieved_ids) if retrieved_ids else 0)
        rr = 0.0
        for rank, sid in enumerate(retrieved_ids, start=1):
            if sid in expected:
                rr = 1.0 / rank
                break
        reciprocal_ranks.append(rr)
        violation = any(sid in retrieved_ids for sid in absent)
        absent_violations.append(1 if violation else 0)
    n = len(ground_truth)
    return {
        'n_queries': n,
        'hit_rate': round(sum(hits) / n, 4),
        'precision_at_5': round(sum(precisions) / n, 4),
        'mean_reciprocal_rank': round(sum(reciprocal_ranks) / n, 4),
        'absent_violation_rate': round(sum(absent_violations) / n, 4),
    }


if __name__ == '__main__':
    print('Loading ground truth and personas...')
    ground_truth = load_ground_truth()
    personas = load_personas()
    print('Initializing recommendation engine...')
    engine = RecommendationEngine()
    print(f'Evaluating {len(ground_truth)} queries...')
    metrics = evaluate(engine, ground_truth, personas)
    print('\n=== EVALUATION RESULTS ===')
    for k, v in metrics.items():
        print(f'  {k}: {v}')
