from __future__ import annotations

import time
from pathlib import Path
from uuid import uuid4

import pyttsx3


def _wait_for_audio(path: Path, timeout_sec: float = 10.0) -> None:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if path.exists() and path.stat().st_size > 44:
            return
        time.sleep(0.1)
    raise RuntimeError("TTS audio file was not generated in time.")


def speak(text: str, out_dir: Path | None = None) -> str:
    """
    Generate real speech with pyttsx3 and return the saved wav path.
    """
    if not text.strip():
        raise ValueError("Cannot synthesize empty text.")

    if out_dir is None:
        out_dir = Path.cwd() / "data" / "tts_audio"
    out_dir.mkdir(parents=True, exist_ok=True)

    outfile = out_dir / f"{uuid4().hex}.wav"

    engine = pyttsx3.init()
    engine.setProperty("rate", 175)
    engine.save_to_file(text, str(outfile))
    engine.runAndWait()
    engine.stop()

    _wait_for_audio(outfile)
    return str(outfile)
