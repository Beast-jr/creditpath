from core.assessment_pipeline import AssessmentPipeline
from core.recommendation.engine import RecommendationEngine

_assessment_pipeline: AssessmentPipeline | None = None
_recommendation_engine: RecommendationEngine | None = None


def set_assessment_pipeline(pipeline: AssessmentPipeline) -> None:
    global _assessment_pipeline
    _assessment_pipeline = pipeline


def set_recommendation_engine(engine: RecommendationEngine) -> None:
    global _recommendation_engine
    _recommendation_engine = engine


def get_assessment_pipeline() -> AssessmentPipeline:
    if _assessment_pipeline is None:
        raise RuntimeError("AssessmentPipeline not initialized.")
    return _assessment_pipeline


def get_recommendation_engine() -> RecommendationEngine:
    if _recommendation_engine is None:
        raise RuntimeError("RecommendationEngine not initialized.")
    return _recommendation_engine
