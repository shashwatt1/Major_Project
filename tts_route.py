from fastapi import APIRouter, File, UploadFile

router = APIRouter()

@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    # save file temp -> call modules.stt.transcribe(path)
    return {"text": "transcribed text placeholder"}
