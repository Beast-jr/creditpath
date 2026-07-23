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
    def __init__(self) -> None:
        self._recommendation_engine = RecommendationEngine()
        self._clusterer = ProfileClusterer()
        self._llm_client = GeminiClient()
        self._logger = ObservabilityLogger()

    def assess(self, profile: BusinessProfile) -> AssessmentOutput:
        total_start = time.monotonic()

        validate_business_profile(profile)

        t0 = time.monotonic()
        scorecard = score_business(profile)
        scorecard_latency_ms = int((time.monotonic() - t0) * 1000)

        cluster = self._clusterer.assign(profile)

        t0 = time.monotonic()
        explanation = generate_explanation(profile, scorecard, self._llm_client)
        llm_explain_latency_ms = int((time.monotonic() - t0) * 1000)

        t0 = time.monotonic()
        improvement_plan = generate_plan(profile, scorecard, self._llm_client)
        llm_plan_latency_ms = int((time.monotonic() - t0) * 1000)

        t0 = time.monotonic()
        recommendations = self._recommendation_engine.recommend(profile, top_k=5)
        retrieval_latency_ms = int((time.monotonic() - t0) * 1000)

        total_latency_ms = int((time.monotonic() - total_start) * 1000)

        output = AssessmentOutput(
            profile=profile,
            scorecard=scorecard,
            explanation=explanation,
            improvement_plan=improvement_plan,
            recommendations=recommendations,
            cluster=cluster,
        )

        event = AssessmentEvent(
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
