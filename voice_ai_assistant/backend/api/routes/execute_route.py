from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from modules import automator

router = APIRouter()


class ExecuteRequest(BaseModel):
    command: str = Field(..., min_length=1)


@router.post("/run")
def run_command(payload: ExecuteRequest):
    try:
        return automator.execute_command(payload.command)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
