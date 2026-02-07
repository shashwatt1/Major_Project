from pydantic import BaseModel, Field


class LLMRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    user_id: str | None = None


class LLMResponse(BaseModel):
    response: str


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1)


class TTSResponse(BaseModel):
    audio_base64: str | None = None
    audio_path: str | None = None
