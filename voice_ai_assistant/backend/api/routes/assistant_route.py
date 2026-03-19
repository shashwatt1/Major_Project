import base64
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, File, HTTPException, UploadFile

from api.schemas import AssistantResponse
from modules import automator, rag, stt, tts
from modules.crypto_utils import decrypt_bytes, encrypt_audio_to_file, encrypt_text_to_file
from modules.intent_classifier import classify_intent

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data"
AUDIO_DIR = DATA_DIR / "encrypted_audio"
TRANSCRIPT_DIR = DATA_DIR / "encrypted_transcripts"
TTS_DIR = DATA_DIR / "tts_audio"


@router.post("/run", response_model=AssistantResponse)
async def run_assistant(file: UploadFile = File(...)):
    try:
        audio_bytes = await file.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Empty audio file.")

        ext = Path(file.filename or "audio.wav").suffix or ".wav"
        _audio_id, encrypted_audio_path = encrypt_audio_to_file(audio_bytes, AUDIO_DIR, ext)

        decrypted_audio = decrypt_bytes(encrypted_audio_path.read_bytes())
        with NamedTemporaryFile(suffix=ext, delete=True) as tmp:
            tmp.write(decrypted_audio)
            tmp.flush()
            transcript = stt.transcribe(tmp.name)

        encrypt_text_to_file(transcript, TRANSCRIPT_DIR)

        intent = classify_intent(transcript)
        sources: list[dict[str, str]] = []
        command_result: dict | None = None

        if intent == "command":
            command_result = automator.execute_command(transcript)
            response_text = command_result.get("info", "Command executed.")
        else:
            response_text, sources = rag.rag_answer(transcript)

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
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
