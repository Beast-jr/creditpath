from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.dependencies import set_assessment_pipeline, set_recommendation_engine
from core.assessment_pipeline import AssessmentPipeline
from core.recommendation.engine import RecommendationEngine

ALLOWED_ORIGINS = [
    "http://localhost:8501",
    "https://*.streamlit.app",
    "https://creditpath.streamlit.app",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    pipeline = AssessmentPipeline()
    engine = RecommendationEngine()
    set_assessment_pipeline(pipeline)
    set_recommendation_engine(engine)
    yield


app = FastAPI(
    title="CreditPath API",
    description="Loan readiness assessment and government scheme discovery for Indian MSMEs.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
async def health():
    """Liveness check for Railway."""
    return {"status": "ok", "version": "1.0.0"}
