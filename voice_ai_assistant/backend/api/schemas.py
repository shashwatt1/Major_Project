from pydantic import BaseModel, Field


class LLMRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    user_id: str | None = None
    use_rag: bool = False
    top_k: int = 3


class LLMResponse(BaseModel):
    response: str
    sources: list[dict[str, str]] = []


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1)


class TTSResponse(BaseModel):
    audio_base64: str | None = None
    audio_path: str | None = None


class AssistantResponse(BaseModel):
    transcript: str
    intent: str
    response: str
    audio_base64: str
    audio_path: str | None = None
    sources: list[dict[str, str]] = []
    command_result: dict | None = None
