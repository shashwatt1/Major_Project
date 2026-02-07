from fastapi import APIRouter, HTTPException

from api.schemas import LLMRequest, LLMResponse
from modules import llm_client

router = APIRouter()


@router.post("/generate", response_model=LLMResponse)
def generate_response(payload: LLMRequest):
    try:
        response = llm_client.get_response(payload.prompt, payload.user_id)
        return LLMResponse(response=response)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
