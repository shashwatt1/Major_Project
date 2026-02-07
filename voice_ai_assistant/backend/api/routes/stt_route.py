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
    try:
        audio_bytes = await file.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Empty audio file.")

        ext = Path(file.filename or "audio.wav").suffix or ".wav"
        audio_id, _audio_path = encrypt_audio_to_file(audio_bytes, AUDIO_DIR, ext)

        # Decrypt in-memory and write to a temp file for the STT module.
        decrypted_audio = decrypt_bytes(_audio_path.read_bytes())
        with NamedTemporaryFile(suffix=ext, delete=True) as tmp:
            tmp.write(decrypted_audio)
            tmp.flush()
            text = stt.transcribe(tmp.name)

        transcript_id, _transcript_path = encrypt_text_to_file(text, TRANSCRIPT_DIR)

        return {
            "text": text,
            "audio_id": audio_id,
            "transcript_id": transcript_id,
        }
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
