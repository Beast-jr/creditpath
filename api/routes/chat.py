from fastapi import APIRouter, Depends, HTTPException
from api.schemas import ChatRequest, ChatResponse, ChatSourceResponse
from api.dependencies import get_chat_service
from core.rag.chat_service import ChatService
from core.schema import BusinessProfile

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service),
):
    try:
        profile = BusinessProfile(**request.profile.model_dump())
        result = service.answer(
            question=request.question,
            profile=profile,
            weighted_score=request.weighted_score,
            tier=request.tier,
        )
        return ChatResponse(
            answer=result.answer,
            sources=[
                ChatSourceResponse(scheme_name=name, official_url=url)
                for name, url in zip(result.sources, result.source_urls)
            ],
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))