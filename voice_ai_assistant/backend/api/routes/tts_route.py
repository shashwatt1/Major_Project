import base64
from pathlib import Path

from fastapi import APIRouter, HTTPException

from api.schemas import TTSRequest, TTSResponse
from modules import tts

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data"
TTS_DIR = DATA_DIR / "tts_audio"


@router.post("/speak", response_model=TTSResponse)
def speak(payload: TTSRequest):
    try:
        audio_path = tts.speak(payload.text, out_dir=TTS_DIR)
        audio_bytes = Path(audio_path).read_bytes()
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
        return TTSResponse(audio_base64=audio_base64, audio_path=str(audio_path))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
