"""
core/rag/chat_pipeline.py
Assembles context from retrieved chunks + user profile + scores,
calls Gemini once, returns a grounded answer with source citations.
"""

from dataclasses import dataclass
from core.rag.retriever import RetrievedChunk
from core.llm.client import GeminiClient


@dataclass
class ChatResponse:
    answer: str
    sources: list[str]   # scheme names cited
    source_urls: list[str]


def _build_prompt(
    question: str,
    chunks: list[RetrievedChunk],
    profile_summary: str,
    score_summary: str,
) -> str:
    context_blocks = []
    for i, chunk in enumerate(chunks, 1):
        context_blocks.append(
            f"[Source {i}: {chunk.scheme_name} — {chunk.chunk_type}]\n{chunk.text}"
        )
    context = "\n\n".join(context_blocks)

    return f"""You are CreditPath's scheme advisor for Indian MSMEs.
Answer the user's question using ONLY the scheme information provided below.
If the answer is not in the sources, say "I don't have enough information about that."
Always ground your answer in the sources. Be concise and specific.
At the end, list which sources you used as "Sources: [name1, name2]".

--- USER PROFILE ---
{profile_summary}

--- SCORECARD SUMMARY ---
{score_summary}

--- SCHEME INFORMATION ---
{context}

--- QUESTION ---
{question}

--- ANSWER ---"""


def _extract_sources(chunks: list[RetrievedChunk]) -> tuple[list[str], list[str]]:
    seen = set()
    names, urls = [], []
    for chunk in chunks:
        if chunk.scheme_id not in seen:
            seen.add(chunk.scheme_id)
            names.append(chunk.scheme_name)
            urls.append(chunk.official_url)
    return names, urls


def ask(
    question: str,
    chunks: list[RetrievedChunk],
    profile_summary: str,
    score_summary: str,
    llm_client: GeminiClient,
) -> ChatResponse:
    prompt = _build_prompt(question, chunks, profile_summary, score_summary)
    answer = llm_client.generate(prompt)
    names, urls = _extract_sources(chunks)
    return ChatResponse(answer=answer, sources=names, source_urls=urls)