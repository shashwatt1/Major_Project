from __future__ import annotations

from functools import lru_cache

import whisper


@lru_cache(maxsize=1)
def _load_model():
    return whisper.load_model("base")


def transcribe(audio_path: str) -> str:
    """
    Transcribe an audio file with Whisper and return plain text.
    """
    model = _load_model()
    result = model.transcribe(audio_path, fp16=False)
    text = (result.get("text") or "").strip()
    if not text:
        raise ValueError("Whisper could not extract any transcript from the audio.")
    return text
