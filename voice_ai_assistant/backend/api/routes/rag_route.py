from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from modules import rag

router = APIRouter()


class RAGRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = 3


@router.post("/rag_query")
def rag_query(payload: RAGRequest):
    try:
        answer, sources = rag.rag_answer(payload.query, top_k=payload.top_k)
        return {"response": answer, "sources": sources}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
