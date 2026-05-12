import base64
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, File, HTTPException, UploadFile

from api.schemas import AssistantResponse
from modules import automator, rag, stt, tts
from modules.crypto_utils import encrypt_audio_to_file, encrypt_text_to_file
from modules.intent_classifier import classify_intent

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data"
AUDIO_DIR = DATA_DIR / "encrypted_audio"
TRANSCRIPT_DIR = DATA_DIR / "encrypted_transcripts"
TTS_DIR = DATA_DIR / "tts_audio"


@router.post("/run", response_model=AssistantResponse)
async def run_assistant(file: UploadFile = File(...)):
    tmp_path = None
    try:
        audio_bytes = await file.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Empty audio file.")

        # Ensure dirs exist
        AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
        TTS_DIR.mkdir(parents=True, exist_ok=True)

        ext = Path(file.filename or "audio.webm").suffix or ".webm"

        # Encrypt and store the original audio
        encrypt_audio_to_file(audio_bytes, AUDIO_DIR, ext)

        # Write raw audio to temp file for Whisper
        # Use delete=False to avoid macOS premature deletion bug
        with NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        # STT
        transcript = stt.transcribe(tmp_path)

        # Encrypt and store transcript
        encrypt_text_to_file(transcript, TRANSCRIPT_DIR)

        # Intent classification
        intent = classify_intent(transcript)
        sources: list[dict[str, str]] = []
        command_result: dict | None = None

        if intent == "command":
            command_result = automator.execute_command(transcript)
            response_text = command_result.get("info", "Command executed.")
        else:
            # RAG + LLM
            response_text, sources = rag.rag_answer(transcript)

        # TTS
        audio_path = tts.speak(response_text, out_dir=TTS_DIR)
        audio_base64 = base64.b64encode(Path(audio_path).read_bytes()).decode("utf-8")

        return AssistantResponse(
            transcript=transcript,
            intent=intent,
            response=response_text,
            audio_base64=audio_base64,
            audio_path=str(audio_path),
            sources=sources,
            command_result=command_result,
        )

    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}") from exc
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
