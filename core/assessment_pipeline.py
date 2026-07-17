"""Assessment pipeline — orchestrates all components into one assess() call.

Component initialization order (happens once at startup):
  RecommendationEngine  — loads ChromaDB index + embedding model
  ProfileClusterer      — loads cluster model from disk
  GeminiClient          — loads disk cache
  ObservabilityLogger   — opens SQLite connection

Never call assess() before the ChromaDB index and cluster model exist:
  python -m scripts.build_index
  python -m scripts.train_clusters
"""
import time
import uuid
from datetime import datetime, timezone

from core.llm.client import GeminiClient
from core.llm.explainer import generate_explanation
from core.llm.planner import generate_plan
from core.clustering.model import ProfileClusterer
from core.observability import ObservabilityLogger
from core.recommendation.engine import RecommendationEngine
from core.schema import (
    AssessmentEvent,
    AssessmentOutput,
    BusinessProfile,
    validate_business_profile,
)
from core.scorecard.engine import score_business


class AssessmentPipeline:
    """Wires all components into a single assess() call.
    Instantiate once at application startup — not per request.
    """

    def __init__(self) -> None:
        self._recommendation_engine = RecommendationEngine()
        self._clusterer = ProfileClusterer()
        self._llm_client = GeminiClient()
        self._logger = ObservabilityLogger()

    def assess(self, profile: BusinessProfile) -> AssessmentOutput:
        """Run the full assessment pipeline. Returns AssessmentOutput.

        Steps:
          1. validate_business_profile
          2. score_business
          3. ProfileClusterer.assign
          4. generate_explanation   (LLM Call 1)
          5. generate_plan          (LLM Call 2)
          6. RecommendationEngine.recommend
          7. Build AssessmentOutput
          8. ObservabilityLogger.log_assessment
        """
        total_start = time.monotonic()

        # Step 1 — validate
        validate_business_profile(profile)

        # Step 2 — scorecard
        t0 = time.monotonic()
        scorecard = score_business(profile)
        scorecard_latency_ms = int((time.monotonic() - t0) * 1000)

        # Step 3 — cluster
        cluster = self._clusterer.assign(profile)

        # Step 4 — LLM explanation
        t0 = time.monotonic()
        explanation = generate_explanation(profile, scorecard, self._llm_client)
        llm_explain_latency_ms = int((time.monotonic() - t0) * 1000)

        # Step 5 — LLM improvement plan
        t0 = time.monotonic()
        improvement_plan = generate_plan(profile, scorecard, self._llm_client)
        llm_plan_latency_ms = int((time.monotonic() - t0) * 1000)

        # Step 6 — recommendations
        t0 = time.monotonic()
        recommendations = self._recommendation_engine.recommend(profile, top_k=5)
        retrieval_latency_ms = int((time.monotonic() - t0) * 1000)

        total_latency_ms = int((time.monotonic() - total_start) * 1000)

        # Step 7 — build output
        output = AssessmentOutput(
            profile=profile,
            scorecard=scorecard,
            explanation=explanation,
            improvement_plan=improvement_plan,
            recommendations=recommendations,
            cluster=cluster,
        )

        # Step 8 — log (never crashes pipeline)
        event = AssessmentEvent(PYTHONPATH=. python -c "
import json
from core.recommendation.engine import RecommendationEngine
from core.schema import BusinessProfile
personas = json.load(open('tests/fixtures/golden_personas.json'))
engine = RecommendationEngine()
for i, p in enumerate(personas):
    profile = BusinessProfile(**{k: v for k, v in p.items() if k != 'expected_tier'})
    result = engine.recommend(profile, top_k=5)
    ids = [m.scheme.scheme_id for m in result.matches]
    print(i, p['business_name'], '->', ids)
" 2>/dev/null
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            profile=profile,
            scorecard_result=scorecard,
            explanation=explanation,
            improvement_plan=improvement_plan,
            recommendation_result=recommendations,
            cluster_assignment=cluster,
            scorecard_latency_ms=scorecard_latency_ms,
            llm_explain_latency_ms=llm_explain_latency_ms,
            llm_plan_latency_ms=llm_plan_latency_ms,
            retrieval_latency_ms=retrieval_latency_ms,
            total_latency_ms=total_latency_ms,
        )
        self._logger.log_assessment(event)

        return output
