from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.dependencies import (
    set_assessment_pipeline,
    set_recommendation_engine,
    set_chat_service,
)
from api.routes import assessment, recommendation, whatif, chat
from core.assessment_pipeline import AssessmentPipeline
from core.recommendation.engine import RecommendationEngine
from core.rag.chat_service import ChatService
from core.llm.client import GeminiClient

VECTORSTORE_PATH = Path("data/vectorstore")

ALLOWED_ORIGINS = [
    "http://localhost:8501",
    "https://*.streamlit.app",
    "https://creditpath.streamlit.app",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    pipeline = AssessmentPipeline()
    engine = RecommendationEngine()
    chat_service = ChatService(
        vectorstore_path=VECTORSTORE_PATH,
        llm_client=GeminiClient(),
    )

    set_assessment_pipeline(pipeline)
    set_recommendation_engine(engine)
    set_chat_service(chat_service)
    yield


app = FastAPI(
    title="CreditPath API",
    description="Loan readiness assessment and government scheme discovery for Indian MSMEs.",
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(assessment.router)
app.include_router(recommendation.router)
app.include_router(whatif.router)
app.include_router(chat.router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "version": "1.1.0"}
