"""
core/rag/chat_service.py
Core-layer service for the scheme Q&A feature.
Owns the ChromaDB collection and orchestrates retrieve -> generate.
"""

from pathlib import Path
from core.rag.retriever import get_retriever, retrieve
from core.rag.chat_pipeline import ask, ChatResponse
from core.llm.client import GeminiClient
from core.schema import BusinessProfile

DEFAULT_TOP_K = 5


class ChatService:
    """Answers natural language questions about financing schemes."""

    def __init__(self, vectorstore_path: Path, llm_client: GeminiClient):
        self._collection = get_retriever(vectorstore_path)
        self._llm = llm_client

    @staticmethod
    def _format_profile(profile: BusinessProfile) -> str:
        return (
            f"Sector: {profile.sector}\n"
            f"Location: {profile.city}, {profile.state} (tier {profile.geographic_tier})\n"
            f"Monthly revenue: Rs {profile.monthly_revenue_inr:,.0f}\n"
            f"Business vintage: {profile.vintage_months} months\n"
            f"GST filing rate: {profile.gst_filing_rate_pct}%\n"
            f"Has collateral: {'Yes' if profile.has_collateral else 'No'}\n"
            f"Loan amount sought: Rs {profile.loan_amount_sought_inr:,.0f}"
        )

    @staticmethod
    def _format_scores(weighted_score: float | None, tier: str | None) -> str:
        if weighted_score is None and tier is None:
            return "Scorecard not yet run for this business."
        parts = []
        if weighted_score is not None:
            parts.append(f"Overall readiness score: {weighted_score:.0f}/100")
        if tier:
            parts.append(f"Tier: {tier}")
        return ". ".join(parts)

    def answer(
        self,
        question: str,
        profile: BusinessProfile,
        weighted_score: float | None = None,
        tier: str | None = None,
        top_k: int = DEFAULT_TOP_K,
    ) -> ChatResponse:
        chunks = retrieve(question, self._collection, top_k=top_k)
        return ask(
            question=question,
            chunks=chunks,
            profile_summary=self._format_profile(profile),
            score_summary=self._format_scores(weighted_score, tier),
            llm_client=self._llm,
        )