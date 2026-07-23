from core.assessment_pipeline import AssessmentPipeline
from core.recommendation.engine import RecommendationEngine
from core.rag.chat_service import ChatService

_assessment_pipeline: AssessmentPipeline | None = None
_recommendation_engine: RecommendationEngine | None = None
_chat_service: ChatService | None = None


def set_assessment_pipeline(pipeline: AssessmentPipeline) -> None:
    global _assessment_pipeline
    _assessment_pipeline = pipeline


def set_recommendation_engine(engine: RecommendationEngine) -> None:
    global _recommendation_engine
    _recommendation_engine = engine


def set_chat_service(service: ChatService) -> None:
    global _chat_service
    _chat_service = service


def get_assessment_pipeline() -> AssessmentPipeline:
    if _assessment_pipeline is None:
        raise RuntimeError("AssessmentPipeline not initialized.")
    return _assessment_pipeline


def get_recommendation_engine() -> RecommendationEngine:
    if _recommendation_engine is None:
        raise RuntimeError("RecommendationEngine not initialized.")
    return _recommendation_engine


def get_chat_service() -> ChatService:
    if _chat_service is None:
        raise RuntimeError("ChatService not initialized.")
    return _chat_service