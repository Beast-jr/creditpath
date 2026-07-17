import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.recommendation.engine import RecommendationEngine
from core.recommendation.filter import ConstraintFilter
from core.recommendation.retriever import SchemeRetriever
from core.schema import BusinessProfile, RecommendationResult
from eval.run_ragas import load_ground_truth, load_personas, evaluate


class DenseOnlyEngine:
    def __init__(self):
        self._filter = ConstraintFilter()
        self._retriever = SchemeRetriever()

    def recommend(self, profile, top_k=5):
        eligible = self._filter.filter(profile)
        if not eligible:
            return RecommendationResult(matches=[], total_found=0)
        candidate_ids = [s.scheme_id for s in eligible]
        query = f"{profile.sector} {profile.state} {profile.loan_amount_sought_inr}"
        matches = self._retriever.retrieve(query, candidate_ids, k=top_k)
        matches_sorted = sorted(matches, key=lambda m: m.match_score, reverse=True)[:top_k]
        return RecommendationResult(matches=matches_sorted, total_found=len(eligible))


if __name__ == '__main__':
    ground_truth = load_ground_truth()
    personas = load_personas()
    n = len(ground_truth)

    print('=== ABLATION STUDY: Dense-Only vs Hybrid ===\n')

    print('Config A: Dense-only retrieval...')
    dense_engine = DenseOnlyEngine()
    config_a = evaluate(dense_engine, ground_truth, personas)

    print('Config B: Full hybrid pipeline...')
    hybrid_engine = RecommendationEngine()
    config_b = evaluate(hybrid_engine, ground_truth, personas)

    print(f'\n{"Metric":<30} {"Dense-Only":>12} {"Hybrid":>12} {"Delta":>10}')
    print('-' * 66)
    for metric in ['hit_rate', 'precision_at_5', 'mean_reciprocal_rank', 'absent_violation_rate']:
        a = config_a[metric]
        b = config_b[metric]
        delta = round(b - a, 4)
        arrow = 'up' if delta > 0 else ('down' if delta < 0 else '=')
        print(f'  {metric:<28} {a:>12} {b:>12}   {arrow} {abs(delta)}')

    print(f'\n  n_queries: {n}')

    results = {'config_a_dense_only': config_a, 'config_b_hybrid': config_b}
    Path('eval/results').mkdir(exist_ok=True)
    with open('eval/results/ablation_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print('\nResults saved to eval/results/ablation_results.json')
