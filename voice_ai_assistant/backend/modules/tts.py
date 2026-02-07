from pathlib import Path
from uuid import uuid4
import wave


def _write_silence_wav(path: Path, duration_sec: float = 1.0, sample_rate: int = 22050) -> None:
    frames = int(duration_sec * sample_rate)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"\x00\x00" * frames)


def speak(text: str, out_dir: Path | None = None) -> str:
    """
    Convert text to speech. Returns a path to a wav file.
    Falls back to a short silent wav if TTS backend isn't available.
    """
    if out_dir is None:
        out_dir = Path.cwd() / "data" / "tts_audio"
    out_dir.mkdir(parents=True, exist_ok=True)

    outfile = out_dir / f"{uuid4().hex}.wav"

    try:
        import pyttsx3

        engine = pyttsx3.init()
        engine.save_to_file(text, str(outfile))
        engine.runAndWait()
    except Exception:
        _write_silence_wav(outfile)

    return str(outfile)
