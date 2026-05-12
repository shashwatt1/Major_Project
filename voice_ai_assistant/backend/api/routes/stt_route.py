import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, File, HTTPException, UploadFile

from modules import stt
from modules.crypto_utils import decrypt_bytes, encrypt_audio_to_file, encrypt_text_to_file

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data"
AUDIO_DIR = DATA_DIR / "encrypted_audio"
TRANSCRIPT_DIR = DATA_DIR / "encrypted_transcripts"


@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    tmp_path = None
    try:
        audio_bytes = await file.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Empty audio file.")

        ext = Path(file.filename or "audio.webm").suffix or ".webm"

        # Store encrypted copy for audit trail
        AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
        audio_id, _audio_path = encrypt_audio_to_file(audio_bytes, AUDIO_DIR, ext)

        # Write to a temp file WITHOUT delete=True (macOS deletes before Whisper can read)
        with NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        text = stt.transcribe(tmp_path)

        transcript_id, _transcript_path = encrypt_text_to_file(text, TRANSCRIPT_DIR)

        return {
            "text": text,
            "audio_id": audio_id,
            "transcript_id": transcript_id,
        }

    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        # Always clean up temp file
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
