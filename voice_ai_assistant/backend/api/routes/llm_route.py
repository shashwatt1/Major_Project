from fastapi import APIRouter, HTTPException

from api.schemas import LLMRequest, LLMResponse
from modules import llm_client, rag

router = APIRouter()


@router.post("/generate", response_model=LLMResponse)
def generate_response(payload: LLMRequest):
    try:
        if payload.use_rag:
            response, sources = rag.rag_answer(payload.prompt, top_k=payload.top_k, user_id=payload.user_id)
            return LLMResponse(response=response, sources=sources)

        response = llm_client.get_response(payload.prompt, payload.user_id)
        return LLMResponse(response=response, sources=[])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
