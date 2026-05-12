"""
tts.py — Text-to-Speech using macOS built-in 'say' command + ffmpeg.

Why not pyttsx3?
  pyttsx3 on macOS generates AIFF format even with a .wav extension.
  Browsers cannot play AIFF. This module uses:
    1. macOS `say` → generates proper AIFF
    2. ffmpeg → converts AIFF → browser-compatible WAV (16-bit PCM)
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from uuid import uuid4


def speak(text: str, out_dir: Path | None = None) -> str:
    """
    Generate speech audio from text and return the path to a WAV file
    that browsers can play directly.

    Requires: ffmpeg (installed via brew install ffmpeg)
    """
    if not text.strip():
        raise ValueError("Cannot synthesize empty text.")

    if out_dir is None:
        out_dir = Path.cwd() / "data" / "tts_audio"
    out_dir.mkdir(parents=True, exist_ok=True)

    uid = uuid4().hex
    aiff_path = out_dir / f"{uid}_tmp.aiff"
    wav_path = out_dir / f"{uid}.wav"

    try:
        # Step 1: macOS say → AIFF (highest quality, no network required)
        subprocess.run(
            ["say", "-o", str(aiff_path), text],
            check=True,
            timeout=30,
            capture_output=True,
        )

        # Step 2: ffmpeg → convert AIFF to browser-compatible WAV (16-bit, 22050 Hz, mono)
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(aiff_path),
                "-ar", "22050",
                "-ac", "1",
                "-sample_fmt", "s16",
                str(wav_path),
            ],
            check=True,
            timeout=30,
            capture_output=True,
        )

    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode(errors="ignore") if exc.stderr else ""
        raise RuntimeError(f"TTS generation failed: {stderr}") from exc
    except FileNotFoundError as exc:
        raise RuntimeError(
            "TTS requires 'say' (built-in macOS) and 'ffmpeg'. "
            "Install ffmpeg with: brew install ffmpeg"
        ) from exc
    finally:
        # Always clean up the intermediate AIFF file
        if aiff_path.exists():
            aiff_path.unlink(missing_ok=True)

    if not wav_path.exists() or wav_path.stat().st_size < 100:
        raise RuntimeError("TTS produced an empty or invalid audio file.")

    return str(wav_path)
